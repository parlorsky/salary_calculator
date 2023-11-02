import subprocess
import sys

def install(package):
	subprocess.run([sys.executable, '-m', 'pip', 'install', package, '-q'])