import datetime
import json

from pprint import pprint

import github3

from pylab import plot, show, xlabel, ylabel


class Counter(dict):
    def __init__(self, initial=None):
        if initial is not None:
            self.update(initial)

    def increment(self, thing, amount=1):
        self[thing] = self.get(thing, 0) + amount

    def update(self, things):
        for thing in things:
            self.increment(thing)


def print_helpful(thing):
    print(thing)
    pprint(dir(thing))

cfg = json.load(open(".config.json"))
gh = github3.login(cfg["username"], password=cfg["password"])

user = gh.user("meawoppl")

kesm_repo = gh.repository("3scan", "kesm")


def get_prs_since(repo, datetime):
    prs = []
    for n, pr in enumerate(repo.pull_requests(state="closed")):
        print("Scanning:", pr.title)
        possibly_needs_convestion = pr.created_at.replace(tzinfo=None)
        # Skip unmerged (closed/wo code)
        if not pr.merged_at:
            print("", "Skipped:", pr.title)
            continue

        if possibly_needs_convestion < datetime:
            break

        prs.append(pr)

    return prs

a_month_ago = datetime.datetime.now() - datetime.timedelta(weeks=16)
kesm_prs = get_prs_since(kesm_repo, a_month_ago)


def compute_files_diff(files_list):
    adds = sum(file.additions for file in files_list)
    dels = sum(file.deletions for file in files_list)

    return adds, dels


def compute_pr_stats(pr_list):
    # Number of PR's per user
    user_pr_count = Counter()
    user_add_lines = Counter()
    user_del_lines = Counter()

    for pr in pr_list:
        user = pr.user.login
        user_pr_count.increment(user)

        adds, dels = compute_files_diff(list(pr.files()))

        # pprint(pr.as_dict())
        user_add_lines.increment(user, adds)
        user_del_lines.increment(user, dels)

        time_open = pr.merged_at - pr.created_at
        review_time = time_open.total_seconds() / (3600 * 24)
        changes = adds - dels
        time_per_line_change = changes / review_time
        print(review_time, adds)

        plot([review_time], [adds], "go", markersize=15, alpha=0.7)
        plot([review_time], [dels], "ro", markersize=15, alpha=0.7)

    xlabel("Review Time (Days)")
    ylabel("Change Count (adds+dels)")
    show()
    # Time from open to close

    for user in user_pr_count:
        print(user, "+%i-%i" % (user_add_lines[user], user_del_lines[user]))

    return user_pr_count, user_add_lines, user_del_lines


pprint(compute_pr_stats(kesm_prs))


# def suggest_pr_reviewer(pr):
#     for file in pr.files():
#         print(file.filename)
#         print_helpful()
#     # Get the files changed

#     pass

#     # blame them
#     # Return user that meets blame stats


# suggest_pr_reviewer(recent_pr)

# for member in list(gh.organization("3scan").members()):
#     print(member.login)
#     # print_helpful(member.login)

# pr = gh.pull_request("3scan", "kesm", 5)
# print_helpful(pr)

print(gh.ratelimit_remaining)
