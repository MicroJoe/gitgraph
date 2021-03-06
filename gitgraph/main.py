import os
import sys
import datetime

import pygit2


def days_range(start, end):
    """Build a range of days from start to end."""
    delta = end - start

    # We start with a negative value so that the offset will be 0 at the first
    # loop iteration.
    offset = datetime.timedelta(days=-1)
    a_day = datetime.timedelta(days=1)

    for _ in range(abs(delta.days) + 1):

        offset += a_day

        # We handle the case where the delta can be negative so we need to
        # decrease days insted of increasing.
        val = start + offset if delta.days > 0 else start - offset

        yield val


def compute_color(nb, m):
    """Compute the color of a cell.

    Args:
        nb: number of commits
        m: maximum number of commits

    Returns:
        string containing color code in HTML format, eg. "#1e6823"

    """
    colors = {
        '0.75' : '1e6823',
        '0.50' : '44a340',
        '0.25' : '8cc665',
        '0.00'   : 'd6e685',
    }

    # Compute ratio
    if m > 0:
        ratio = nb / m
    else:
        ratio = 0

    # Assign default color
    color = 'eee'

    # Select color based on intervals
    for limit, col in colors.items():
        if ratio > float(limit):
            color = col
            break

    return '#{}'.format(color)


def retrieve_repo_activity(repo):
    """Extract some relevant information from a git repository.

    Args:
        repo: an openned pygit2 repository instance

    Returns:
        A dictionnary with useful extracted metadata

    """

    # Retrieve last commit from repo as start point for walk
    last = repo[repo.head.target]

    # Initialize data we are going to return
    nb_commits = 0
    per_day_commits = {}

    # Walks though all the repository's commits by time
    previous_date = None
    for commit in repo.walk(last.id, pygit2.GIT_SORT_TIME):
        commit_date = datetime.datetime.fromtimestamp(commit.commit_time).date()
        today_date = datetime.date.today()

        delta = today_date - commit_date

        if delta.days not in per_day_commits:
            per_day_commits[delta.days] = {
                'date': commit_date,
                'commits': 0
            }

        per_day_commits[delta.days]['commits'] += 1
        nb_commits += 1
        previous_date = commit_date

    # We retrieve first and last commit date
    first = previous_date
    last = datetime.date.today()

    # We generate a list of all days since first commit and fill it with
    # retrieved data.
    continuous_days_commits = []

    for day in days_range(first, last):
        delta = (last - day).days

        if delta in per_day_commits:
            commits = per_day_commits[delta]['commits']
        else:
            commits = 0

        continuous_days_commits.append({
            'date': day,
            'commits': commits
        })

    return {
        'per_day_commits': per_day_commits,
        'continuous_days_commits': reversed(continuous_days_commits),
        'nb_commits': nb_commits
    }


def draw_activity(days, f=sys.stdout):
    """Draw activity graph on file output in SVG format.

    Args:
        days: list of days containing metadata like commits and real date
        f: file output, default is stdout

    """

    weeks = 24
    days = list(reversed(days))[-(weeks*7):]

    box_height = 11
    box_width = 11
    max_commits = max([d['commits'] for d in days])
    spacing = 2
    vertical_boxes = 7

    height = int(box_height * (vertical_boxes + spacing))
    width = int((len(days) / vertical_boxes + 1) * (box_width + spacing))

    print(
        '<?xml version="1.0" encoding="utf-8" ?>'
        '<svg xmlns="http://www.w3.org/2000/svg" width="{}" height="{}">'
        '<title>test</title>'.format(width, height),
        file=f
    )

    for n, day in enumerate(days):
        x = int(n / vertical_boxes) * (box_width + spacing)
        y = (n % vertical_boxes) * (box_height + spacing)

        date = day['date']

        print(
            '<g>'
            '<rect x="{}" y="{}" width="10" height="10" style="fill:{};{}" />'
            '<title>{}\n{}</title>'
            '</g>'
            .format(
                x, y,
                compute_color(day['commits'], max_commits),
                "stroke-width:1px;stroke:red" if n == len(days) - 1 else "",
                date,
                '{} commits'.format(day['commits'])
            ),
            file=f
        )

    print('</svg>')


def usage():
    """Display an usage notice to the user."""
    print('usage: gitgraph.py DIRECTORY', file=sys.stderr)


def run():
    """Run the gitgraph main app."""
    if len(sys.argv) != 2:
        usage()
        sys.exit(1)

    path = sys.argv[1]

    try:
        gitpath = pygit2.discover_repository(path)
    except KeyError:
        msg = 'git repository not found in {}, aborting.'.format(path)
        print(msg, file=sys.stderr)
        sys.exit(1)

    repo = pygit2.Repository(gitpath)

    data = retrieve_repo_activity(repo)['continuous_days_commits']
    draw_activity([day for day in data])


if __name__ == "__main__":
    run()
