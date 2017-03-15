#!/usr/bin/env python

import datetime
import itertools
import json

from pprint import pprint

import pandas as pd
from pandas.tseries.offsets import BusinessHour
import github3
from sklearn import linear_model
# from sklearn.preprocessing import PolynomialFeatures
import numpy as np
from pylab import plot, show, xlabel, ylabel
from pytz import timezone

LOCAL_TZ = timezone("US/Pacific")

# pd.set_option('display.height', 500)
pd.set_option("display.max_rows", 500)
pd.set_option("display.max_columns", 200)
pd.set_option("display.width", 240)


def print_helpful(thing):
    print(thing)
    pprint(dir(thing))


def get_prs_since(repo, datetime):
    prs = []
    for n, pr in enumerate(repo.pull_requests(state="closed")):
        print("Scanning:", pr.title)
        needs_consideration = pr.created_at.replace(tzinfo=None)
        # Skip unmerged (closed/wo code)
        if not pr.merged_at:
            print("", "Skipped:", pr.title)
            continue

        if needs_consideration < datetime:
            break

        prs.append(pr)

    return prs


def print_lm(thing1, thing2, description):
    thing1 = np.asarray(thing1).reshape((-1, 1))
    thing2 = np.asarray(thing2).reshape((-1, 1))
    lm = linear_model.LinearRegression().fit(thing1, thing2)

    print(description)
    print(lm.coef_, lm.intercept_)


def compute_files_diff(files_list):
    adds = sum(file.additions for file in files_list)
    dels = sum(file.deletions for file in files_list)
    return adds, dels, len(files_list)


def sort_comments(list_of_comments):
    return sorted(list_of_comments, key=lambda c: c.created_at)


def compute_buisness_hour_delta(start_dt, end_dt):
    # MRG NOTE: Nasty + slow
    assert start_dt < end_dt
    print(start_dt, start_dt.tzinfo, end_dt.tzinfo)
    for mins in itertools.count():
        if start_dt + BusinessHour(0) + datetime.timedelta(minutes=mins) > end_dt:
            break
    return datetime.timedelta(minutes=mins)


def compute_pr_stats(pr_list):
    data_rows = []
    for pr in pr_list:
        # +- of code
        adds, dels, file_count = compute_files_diff(list(pr.files()))

        # Sift through comments to get comment count/date
        review_comments = list(pr.review_comments())
        issue_comments = list(pr.issue().comments())
        all_comments = sort_comments(review_comments + issue_comments)

        # Time created
        created_dt = pr.created_at.astimezone(LOCAL_TZ)

        # Time merged
        merged_dt = pr.merged_at.astimezone(LOCAL_TZ)

        # Time to first comment
        if len(all_comments) == 0:
            feedback_dt = merged_dt
        else:
            feedback_dt = all_comments[0].created_at.astimezone(LOCAL_TZ)

        feedback_delta = compute_buisness_hour_delta(created_dt, feedback_dt)
        total_delta = compute_buisness_hour_delta(created_dt, merged_dt)

        # Review comments
        comments = len(issue_comments) + len(review_comments)

        data_rows.append((
            pr.user.login,
            feedback_delta,
            total_delta,
            comments,
            adds,
            dels,
            file_count))

    return pd.DataFrame.from_records(
        data_rows,
        columns=(
            "user",
            "time_feedback",
            "time_open",
            "comments",
            "adds",
            "dels",
            "file_count"))

cfg = json.load(open(".config.json"))
gh = github3.login(cfg["username"], password=cfg["password"])

user = gh.user("meawoppl")
kesm_repo = gh.repository("3scan", "kesm")

this_morning = datetime.datetime.now() - datetime.timedelta(hours=1)
kesm_prs = get_prs_since(kesm_repo, this_morning)
kesm_stats = compute_pr_stats(kesm_prs)
pprint(kesm_stats)
print("PR's")
print(kesm_stats.groupby("user").count())

print("Lines added")
print(kesm_stats.groupby("user")["adds"].sum())

print("Time PR is open")
print(kesm_stats.groupby("user")["time_open"].sum() / kesm_stats.groupby("user")["time_open"].count())

print("Time to PR feedback")
print(kesm_stats.groupby("user")["time_feedback"].sum() / kesm_stats.groupby("user")["time_feedback"].count())

print_lm(kesm_stats["time_open"].map(lambda dt: dt.total_seconds() / 3600), kesm_stats["adds"], "add-to")
print_lm(kesm_stats["time_open"].map(lambda dt: dt.total_seconds() / 3600), kesm_stats["file_count"], "filec-to")

# def print_stats(dataframe):
#     xlabel("Review Time (Days)")
#     ylabel("Change Count (adds+dels)")

#     times, comments, adds, dels = np.array(time_effort_adds_dels).T

#     print_lm(adds / 100, times, "Time To Review/HLA")
#     print_lm(adds / 100, comments, "Revied comments/HLA")

#     for user in user_pr_count:
#         print(user, "+%i-%i" % (user_add_lines[user], user_del_lines[user]))

#     show()
#     return user_pr_count, user_add_lines, user_del_lines


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
