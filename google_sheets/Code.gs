/**
 * Google Apps Script for Wyckoff Stock Screener Validation & Forward Testing Ledger.
 * 
 * Provides automated daily candle evaluation, MFE/MAE calculation, target/stop hit detection,
 * same-day ambiguity handling, and real-time research dashboard updates directly in Google Sheets.
 */

// Custom Menu on Sheet Open
function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('📊 Wyckoff Screener')
    .addItem('▶️ Evaluate All Signals & Update Dashboard', 'evaluateAllSignals')
    .addItem('🔄 Refresh Market Data (GOOGLEFINANCE)', 'refreshMarketData')
    .addSeparator()
    .addItem('ℹ️ View System Instructions', 'showInstructions')
    .addToUi();
}

/**
 * Main evaluation function: iterates over SIGNALS tab and populates TEST_RESULTS & DASHBOARD.
 */
function evaluateAllSignals() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var signalsSheet = ss.getSheetByName('SIGNALS');
  var resultsSheet = ss.getSheetByName('TEST_RESULTS');
  var settingsSheet = ss.getSheetByName('SETTINGS');
  var dashboardSheet = ss.getSheetByName('DASHBOARD');

  if (!signalsSheet || !resultsSheet) {
    SpreadsheetApp.getUi().alert('Error: SIGNALS or TEST_RESULTS sheet not found.');
    return;
  }

  // 1. Read Settings
  var settings = getSettingsMap(settingsSheet);
  var maxHoldingDays = settings['Max_Holding_Days'] || 60;
  var frictionPct = settings['Friction_Round_Trip_Pct'] || 0.40;
  var ambiguityHandling = settings['Same_Day_Ambiguity_Handling'] || 'CONSERVATIVE';

  // 2. Read Signals
  var signalData = signalsSheet.getDataRange().getValues();
  if (signalData.length <= 1) {
    SpreadsheetApp.getUi().alert('No signals found in SIGNALS sheet.');
    return;
  }

  var headers = signalData[0];
  var colMap = {};
  for (var c = 0; c < headers.length; c++) {
    colMap[headers[c]] = c;
  }

  var resultsRows = [];
  var winsCount = 0;
  var lossCount = 0;
  var totalEvaluated = 0;
  var totalNetReturn = 0;
  var winReturnsSum = 0;
  var lossReturnsSum = 0;
  var mfeSum = 0;
  var maeSum = 0;
  var targetHitsCount = 0;
  var stopHitsCount = 0;

  for (var r = 1; r < signalData.length; r++) {
    var row = signalData[r];
    var symbol = String(row[colMap['Symbol']]);
    var signalDateStr = formatDate(row[colMap['Signal_Date']]);
    var entryPrice = Number(row[colMap['Entry_Price']]) || 0;
    var stopPrice = Number(row[colMap['Stop_Price']]) || (entryPrice * 0.95);
    var targetPrice = Number(row[colMap['Target_1']]) || (entryPrice * 1.15);
    var score = Number(row[colMap['Screener_Score']]) || 0;
    var priority = String(row[colMap['Priority']] || '');
    var eventType = String(row[colMap['Wyckoff_Event']] || '');
    var signalId = String(row[colMap['Signal_ID']] || (symbol + '_' + signalDateStr));

    if (!symbol || entryPrice <= 0) continue;

    var riskPerShare = Math.max(entryPrice - stopPrice, 0.001 * entryPrice);
    var initialRiskPct = (riskPerShare / entryPrice) * 100.0;

    // Fetch Daily OHLC from GOOGLEFINANCE or Price Data
    var ohlcBars = fetchDailyOHLC(symbol, signalDateStr, maxHoldingDays);
    
    var evalOutcome = evaluateSingleTrade(
      symbol, signalDateStr, entryPrice, stopPrice, targetPrice,
      riskPerShare, initialRiskPct, ohlcBars, maxHoldingDays,
      ambiguityHandling, frictionPct
    );

    // Collect result for TEST_RESULTS sheet
    resultsRows.push([
      signalId, symbol, signalDateStr, evalOutcome.entryDate,
      round2(entryPrice), round2(stopPrice), round2(targetPrice),
      round2(riskPerShare), round2(initialRiskPct),
      evalOutcome.exitDate, evalOutcome.exitPrice ? round2(evalOutcome.exitPrice) : '',
      evalOutcome.exitReason, evalOutcome.holdingDays,
      round2(evalOutcome.netReturnPct), round2(evalOutcome.rMultiple),
      evalOutcome.outcome, round2(evalOutcome.mfePct), round2(evalOutcome.maePct),
      evalOutcome.fwd5d ? round2(evalOutcome.fwd5d) : '',
      evalOutcome.fwd10d ? round2(evalOutcome.fwd10d) : '',
      evalOutcome.fwd20d ? round2(evalOutcome.fwd20d) : '',
      evalOutcome.fwd30d ? round2(evalOutcome.fwd30d) : '',
      evalOutcome.fwd60d ? round2(evalOutcome.fwd60d) : '',
      evalOutcome.targetHit, evalOutcome.stopHit,
      evalOutcome.targetBeforeStop, evalOutcome.stopBeforeTarget,
      evalOutcome.isAmbiguous, evalOutcome.daysToTarget || '', evalOutcome.daysToStop || ''
    ]);

    // Update SIGNALS row output
    signalsSheet.getRange(r + 1, colMap['Exit_Date'] + 1).setValue(evalOutcome.exitDate || '');
    signalsSheet.getRange(r + 1, colMap['Exit_Price'] + 1).setValue(evalOutcome.exitPrice || '');
    signalsSheet.getRange(r + 1, colMap['Return_Pct'] + 1).setValue(round2(evalOutcome.netReturnPct));
    signalsSheet.getRange(r + 1, colMap['R_Multiple'] + 1).setValue(round2(evalOutcome.rMultiple));
    signalsSheet.getRange(r + 1, colMap['Days_Held'] + 1).setValue(evalOutcome.holdingDays);
    signalsSheet.getRange(r + 1, colMap['Outcome'] + 1).setValue(evalOutcome.outcome);

    if (evalOutcome.outcome === 'WIN') {
      winsCount++;
      winReturnsSum += evalOutcome.netReturnPct;
    } else if (evalOutcome.outcome === 'LOSS') {
      lossCount++;
      lossReturnsSum += Math.abs(evalOutcome.netReturnPct);
    }
    if (evalOutcome.targetHit) targetHitsCount++;
    if (evalOutcome.stopHit) stopHitsCount++;
    totalNetReturn += evalOutcome.netReturnPct;
    mfeSum += evalOutcome.mfePct;
    maeSum += evalOutcome.maePct;
    totalEvaluated++;
  }

  // 3. Write to TEST_RESULTS Sheet
  if (resultsRows.length > 0) {
    resultsSheet.getRange(2, 1, resultsSheet.getLastRow() > 1 ? resultsSheet.getLastRow() - 1 : 1, 30).clearContent();
    resultsSheet.getRange(2, 1, resultsRows.length, resultsRows[0].length).setValues(resultsRows);
  }

  // 4. Update DASHBOARD Sheet
  if (dashboardSheet && totalEvaluated > 0) {
    var winRate = (winsCount / totalEvaluated) * 100.0;
    var avgReturn = totalNetReturn / totalEvaluated;
    var profitFactor = lossReturnsSum > 0 ? (winReturnsSum / lossReturnsSum) : 0;
    var avgWin = winsCount > 0 ? (winReturnsSum / winsCount) : 0;
    var avgLoss = lossCount > 0 ? (lossReturnsSum / lossCount) : 0;

    var dashUpdates = [
      ['Total Signals Tested', totalEvaluated, 'Evaluated trade count'],
      ['Total Wins', winsCount, 'Trades with net return > 0'],
      ['Total Losses', lossCount, 'Trades with net return < 0'],
      ['Win Rate (%)', round2(winRate), 'Percentage of winning trades'],
      ['Average Net Return (%)', round2(avgReturn), 'Mean net return (0.40% friction deducted)'],
      ['Average Winner (%)', round2(avgWin), 'Mean gain on winning trades'],
      ['Average Loser (%)', round2(avgLoss), 'Mean loss on losing trades'],
      ['Profit Factor', round2(profitFactor), 'Gross wins / Gross losses'],
      ['Average MFE (%)', round2(mfeSum / totalEvaluated), 'Average Maximum Favorable Excursion'],
      ['Average MAE (%)', round2(maeSum / totalEvaluated), 'Average Maximum Adverse Excursion'],
      ['Target Hit Rate (%)', round2((targetHitsCount / totalEvaluated) * 100.0), 'Percentage hitting Target 1'],
      ['Stop Hit Rate (%)', round2((stopHitsCount / totalEvaluated) * 100.0), 'Percentage hitting Stop Loss']
    ];
    dashboardSheet.getRange(2, 1, dashUpdates.length, 3).setValues(dashUpdates);
  }

  SpreadsheetApp.getUi().alert('✅ Evaluated ' + totalEvaluated + ' signals successfully!\nWin Rate: ' + (winsCount/totalEvaluated*100).toFixed(1) + '%\nResults updated in TEST_RESULTS & DASHBOARD.');
}

/**
 * Evaluates a single trade across forward daily candles.
 */
function evaluateSingleTrade(symbol, signalDate, entryPrice, stopPrice, targetPrice, riskPerShare, initialRiskPct, ohlcBars, maxDays, ambiguityHandling, frictionPct) {
  var outcome = {
    entryDate: '', exitDate: '', exitPrice: null, exitReason: 'PENDING',
    holdingDays: 0, netReturnPct: 0, rMultiple: 0, outcome: 'PENDING',
    mfePct: 0, maePct: 0, fwd5d: null, fwd10d: null, fwd20d: null, fwd30d: null, fwd60d: null,
    targetHit: false, stopHit: false, targetBeforeStop: false, stopBeforeTarget: false,
    isAmbiguous: false, daysToTarget: null, daysToStop: null
  };

  if (!ohlcBars || ohlcBars.length === 0) {
    return outcome;
  }

  outcome.entryDate = ohlcBars[0].date;
  var actualEntry = entryPrice || ohlcBars[0].open;
  var mfe = 0;
  var mae = 0;
  var evalLen = Math.min(ohlcBars.length, maxDays);

  for (var i = 0; i < evalLen; i++) {
    var bar = ohlcBars[i];
    var dayNum = i + 1;
    var high = bar.high;
    var low = bar.low;
    var close = bar.close;

    var dayMfe = ((high - actualEntry) / actualEntry) * 100.0;
    var dayMae = ((low - actualEntry) / actualEntry) * 100.0;
    if (dayMfe > mfe) mfe = dayMfe;
    if (dayMae < mae) mae = dayMae;

    if (dayNum === 5) outcome.fwd5d = ((close - actualEntry) / actualEntry) * 100.0 - frictionPct;
    if (dayNum === 10) outcome.fwd10d = ((close - actualEntry) / actualEntry) * 100.0 - frictionPct;
    if (dayNum === 20) outcome.fwd20d = ((close - actualEntry) / actualEntry) * 100.0 - frictionPct;
    if (dayNum === 30) outcome.fwd30d = ((close - actualEntry) / actualEntry) * 100.0 - frictionPct;
    if (dayNum === 60) outcome.fwd60d = ((close - actualEntry) / actualEntry) * 100.0 - frictionPct;

    var hitT = high >= targetPrice;
    var hitS = low <= stopPrice;

    if (hitT && !outcome.daysToTarget) {
      outcome.daysToTarget = dayNum;
      outcome.targetHit = true;
    }
    if (hitS && !outcome.daysToStop) {
      outcome.daysToStop = dayNum;
      outcome.stopHit = true;
    }

    if (outcome.exitDate) continue;

    if (hitT && hitS) {
      outcome.isAmbiguous = true;
      if (ambiguityHandling === 'CONSERVATIVE' || ambiguityHandling === 'STOP_FIRST') {
        outcome.exitDate = bar.date;
        outcome.exitPrice = stopPrice;
        outcome.exitReason = 'AMBIGUOUS_SAME_DAY_STOP';
        outcome.holdingDays = dayNum;
        outcome.stopBeforeTarget = true;
      } else if (ambiguityHandling === 'TARGET_FIRST') {
        outcome.exitDate = bar.date;
        outcome.exitPrice = targetPrice;
        outcome.exitReason = 'AMBIGUOUS_SAME_DAY_TARGET';
        outcome.holdingDays = dayNum;
        outcome.targetBeforeStop = true;
      }
    } else if (hitT) {
      outcome.targetHit = true;
      outcome.targetBeforeStop = true;
      outcome.exitDate = bar.date;
      outcome.exitPrice = targetPrice;
      outcome.exitReason = 'TARGET_HIT';
      outcome.holdingDays = dayNum;
    } else if (hitS) {
      outcome.stopHit = true;
      outcome.stopBeforeTarget = true;
      outcome.exitDate = bar.date;
      outcome.exitPrice = stopPrice;
      outcome.exitReason = 'STOP_HIT';
      outcome.holdingDays = dayNum;
    }
  }

  if (!outcome.exitDate && evalLen > 0) {
    var lastBar = ohlcBars[evalLen - 1];
    outcome.exitDate = lastBar.date;
    outcome.exitPrice = lastBar.close;
    outcome.exitReason = 'TIME_HORIZON_REACHED';
    outcome.holdingDays = evalLen;
  }

  outcome.mfePct = mfe;
  outcome.maePct = mae;

  if (outcome.exitPrice !== null) {
    var gross = ((outcome.exitPrice - actualEntry) / actualEntry) * 100.0;
    outcome.netReturnPct = gross - frictionPct;
    outcome.rMultiple = riskPerShare > 0 ? ((outcome.exitPrice - actualEntry) / riskPerShare) : 0;
    outcome.outcome = outcome.netReturnPct > 0 ? 'WIN' : (outcome.netReturnPct < 0 ? 'LOSS' : 'BREAKEVEN');
  }

  return outcome;
}

/**
 * Helper to fetch daily OHLC from GOOGLEFINANCE or Yahoo Finance API.
 */
function fetchDailyOHLC(symbol, signalDateStr, maxDays) {
  var ohlc = [];
  try {
    var ticker = symbol.indexOf(':') > -1 ? symbol : ('NSE:' + symbol);
    var startDate = new Date(signalDateStr);
    startDate.setDate(startDate.getDate() + 1); // strictly AFTER signal date (T+1)
    var endDate = new Date(startDate);
    endDate.setDate(endDate.getDate() + (maxDays * 1.6)); // approximate trading calendar days

    // Attempt GOOGLEFINANCE via hidden calculation sheet or direct fetch
    // Apps Script can query Yahoo Finance JSON API for NSE tickers:
    var cleanSym = symbol.replace('NSE:', '');
    var url = 'https://query1.finance.yahoo.com/v8/finance/chart/' + cleanSym + '.NS?interval=1d&range=3mo';
    var response = UrlFetchApp.fetch(url, { muteHttpExceptions: true });
    if (response.getResponseCode() === 200) {
      var json = JSON.parse(response.getContentText());
      var result = json.chart.result[0];
      var timestamps = result.timestamp;
      var quotes = result.indicators.quote[0];

      for (var t = 0; t < timestamps.length; t++) {
        var barDt = new Date(timestamps[t] * 1000);
        var bStr = Utilities.formatDate(barDt, 'Asia/Kolkata', 'yyyy-MM-dd');
        if (bStr > signalDateStr && quotes.open[t] !== null && quotes.high[t] !== null) {
          ohlc.push({
            date: bStr,
            open: quotes.open[t],
            high: quotes.high[t],
            low: quotes.low[t],
            close: quotes.close[t]
          });
        }
      }
    }
  } catch (e) {
    Logger.log('Market data fetch error for ' + symbol + ': ' + e.message);
  }
  return ohlc;
}

function getSettingsMap(sheet) {
  var map = {};
  if (!sheet) return map;
  var data = sheet.getDataRange().getValues();
  for (var i = 1; i < data.length; i++) {
    map[data[i][0]] = data[i][1];
  }
  return map;
}

function formatDate(val) {
  if (val instanceof Date) {
    return Utilities.formatDate(val, 'Asia/Kolkata', 'yyyy-MM-dd');
  }
  return String(val).substring(0, 10);
}

function round2(num) {
  return typeof num === 'number' ? Math.round(num * 100) / 100 : num;
}

function refreshMarketData() {
  SpreadsheetApp.getUi().alert('Refreshing market data...');
  evaluateAllSignals();
}

function showInstructions() {
  var msg = '📊 WYCKOFF SCREENER VALIDATION SYSTEM\n\n' +
    '1. Paste new candidate rows into the SIGNALS tab.\n' +
    '2. Click "Wyckoff Screener" -> "Evaluate All Signals & Update Dashboard".\n' +
    '3. The system fetches daily OHLC data, tracks targets & stops, and updates the DASHBOARD.\n\n' +
    'For full documentation, see docs/PHASE_18_GOOGLE_SHEETS_VALIDATION.md.';
  SpreadsheetApp.getUi().alert(msg);
}
