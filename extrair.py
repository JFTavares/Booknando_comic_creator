import yaml
with open('bone.yaml') as f:
    # use safe_load instead load
    metadados = yaml.safe_load(f)

print(metadados['title'])