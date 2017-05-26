# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "loan_management"
app_title = "Loan Management"
app_publisher = "Sione Taumoepeau"
app_description = "App for Customer Loan"
app_icon = "octicon octicon-file-directory"
app_color = "red"
app_email = "sione.taumoepeau@gmail.com"
app_license = "MIT"

# Includes in <head>
# ------------------
fixtures = ["Custom Field", "Custom Script", "Print Format"]
# include js, css files in header of desk.html
# app_include_css = "/assets/loan_management/css/loan_management.css"
# app_include_js = "/assets/loan_management/js/loan_management.js"

# include js, css files in header of web template
# web_include_css = "/assets/loan_management/css/loan_management.css"
# web_include_js = "/assets/loan_management/js/loan_management.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "loan_management.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "loan_management.install.before_install"
# after_install = "loan_management.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "loan_management.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"loan_management.tasks.all"
# 	],
# 	"daily": [
# 		"loan_management.tasks.daily"
# 	],
# 	"hourly": [
# 		"loan_management.tasks.hourly"
# 	],
# 	"weekly": [
# 		"loan_management.tasks.weekly"
# 	]
# 	"monthly": [
# 		"loan_management.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "loan_management.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "loan_management.event.get_events"
# }

