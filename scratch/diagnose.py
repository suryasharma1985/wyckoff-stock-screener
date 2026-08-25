import subprocess

cmd = 'powershell "Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, CPU, WorkingSet64, Responding | Format-Table -AutoSize"'
out = subprocess.check_output(cmd, shell=True, text=True)
print(out)
