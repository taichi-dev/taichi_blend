import os
import zipfile

repo_dir = os.path.dirname(__file__)

target_py = os.path.join(repo_dir, 'build', 'bundle_dev.py')

with open(target_py, 'w') as f:
    f.write(template)


os.chdir(os.path.join(repo_dir, 'build'))
#try: os.unlink(os.path.join())
with zipfile.ZipFile(os.path.join(repo_dir, 'build', 'Taichi-Blend-Dev.zip'), 'w', zipfile.ZIP_DEFLATED) as f:
    f.write(os.path.join(repo_dir, 'build', 'bundle_dev.py'), os.path.join('Taichi-Blend-Dev', '__init__.py'))