import shutil
from pathlib import Path

root = Path("d:/projects/ai-config-skafolding")
src = root / "agent_init"
dst = root / "agentforge"

shutil.copytree(src, dst)
shutil.rmtree(src)
print("renamed agent_init/ -> agentforge/")
