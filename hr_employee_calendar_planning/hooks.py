# -*- coding: utf-8 -*-
# Copyright 2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, SUPERUSER_ID
from collections import defaultdict


def post_init_hook(cr, registry, employees=None):
    """Split current calendars by date ranges and assign new ones for
    having proper initial data.
    """
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        if not employees:
            employees = env['hr.employee'].search([])
        calendars = employees.mapped('calendar_id')
        calendar_obj = env['resource.calendar']
        line_obj = env['resource.calendar.attendance']
        groups = line_obj.read_group(
            [('calendar_id', 'in', calendars.ids)],
            ['calendar_id', 'date_from', 'date_to'],
            ['calendar_id', 'date_from:day', 'date_to:day'],
            lazy=False,
        )
        calendar_mapping = defaultdict(list)
        for group in groups:
            calendar = calendar_obj.browse(group['calendar_id'][0])
            lines = line_obj.search(group['__domain'])
            if len(calendar.attendance_ids) == len(lines):
                # Don't alter calendar, as it's the same
                new_calendar = calendar
            else:
                name = calendar.name + " %s-%s" % (
                    lines[0].date_from, lines[0].date_to,
                )
                attendances = []
                for line in lines:
                    attendances.append((0, 0, {
                        'name': line.name,
                        'dayofweek': line.dayofweek,
                        'hour_from': line.hour_from,
                        'hour_to': line.hour_to,
                    }))
                new_calendar = calendar_obj.create({
                    'name': name,
                    'attendance_ids': attendances,
                })
            calendar_mapping[calendar].append(
                (lines[0].date_from, lines[0].date_to, new_calendar),
            )
        for employee in employees:
            calendar_lines = []
            for data in calendar_mapping[employee.calendar_id]:
                calendar_lines.append((0, 0, {
                    'date_start': data[0],
                    'date_end': data[1],
                    'calendar_id': data[2].id,
                }))
            employee.calendar_id = False
            employee.calendar_ids = calendar_lines
