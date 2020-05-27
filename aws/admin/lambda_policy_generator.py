import sys
from jinja2 import Environment, FileSystemLoader


file_loader = FileSystemLoader('.')
env = Environment(loader=file_loader)

template = env.get_template('lambda_policy.j2')

output = template.render(region=sys.argv[1],
                         account_id=sys.argv[2])
with open('lambda_policy.json', 'w') as f:
    f.write(output)
