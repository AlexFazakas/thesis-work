import sys
from jinja2 import Environment, FileSystemLoader


file_loader = FileSystemLoader('.')
env = Environment(loader=file_loader)

for policy in ['lambda', 'ui']:
    policy_name = policy + '_policy'
    template = env.get_template(policy_name + '.j2')

    output = template.render(region=sys.argv[1],
                            account_id=sys.argv[2])
    with open(policy_name + '.json', 'w') as f:
        f.write(output)