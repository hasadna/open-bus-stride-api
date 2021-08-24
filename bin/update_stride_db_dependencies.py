#!/usr/bin/env python3
import sys
import subprocess


def main(stride_db_commit):
    new_lines = []
    with open('requirements-docker.txt') as f:
        for line in f.readlines():
            if line.startswith('-r https://github.com/hasadna/open-bus-stride-db/raw/'):
                line = '-r https://github.com/hasadna/open-bus-stride-db/raw/{}/requirements.txt\n'.format(stride_db_commit)
            elif line.startswith('https://github.com/hasadna/open-bus-stride-db/archive/'):
                line = 'https://github.com/hasadna/open-bus-stride-db/archive/{}.zip\n'.format(stride_db_commit)
            new_lines.append(line)
    with open('requirements-docker.txt', 'w') as f:
        f.writelines(new_lines)
    with open('open-bus-stride-db-docker-image.txt', 'w') as f:
        f.write('docker.pkg.github.com/hasadna/open-bus-stride-db/open-bus-stride-db:{}'.format(stride_db_commit))
    subprocess.check_call(['git', 'add', 'requirements-docker.txt', 'open-bus-stride-db-docker-image.txt'])


if __name__ == '__main__':
    main(*sys.argv[1:])
