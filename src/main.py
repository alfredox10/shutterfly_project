from dateutil.parser import parse as date_parser
from dateutil import rrule

visit_key = 'SITE_VISIT'
customer_key = 'CUSTOMER'
order_key = 'ORDER'
date_key = 'event_time'
total_amount_key = 'total_amount'

def count_weeks(start, end):
    weeks = rrule.rrule(rrule.WEEKLY, dtstart=start, until=end)
    return weeks.count()

def file_to_data(file_path, events):
    first_loop = True
    with open(file_path) as f:
        for line in f.readlines():
            if first_loop:
                first_loop = False
                line_eval = line.strip()[1:-1]
            else:
                line_eval = line.strip()[:-1]
            ingest(line_eval, events)

def write_output(fname, data):
    with open(fname, 'w') as f:
        for x in data:
            f.write(x[0] + ', ' + str(x[1]) + '\n')

def ingest(e, D):
    dic = eval(e)
    if date_key in dic:
        dic[date_key] = date_parser(dic[date_key])

    customer_id = dic['customer_id'] if dic['type'] != customer_key \
                  else dic['key']

    if customer_id not in D:
        # Create new customer_id
        D[customer_id] = [dic]
    else:
        # Add customer data
        D[customer_id].append(dic)

def topXSimpleLTVCustomers_old(x, D, print_info=False):
    # Left here for documentation purposes, after an email exchange I
    # was told calculating visits was unecessary.

    """
    A simple LTV can be calculated using the following equation: 52(a) x t.
    Where a is the average customer value per week (customer expenditures per
    visit (USD) x number of site visits per week) and t is the average customer lifespan.
    The average lifespan for Shutterfly is 10 years.

    LTV = 52(a) x t
    visits_per_week = count(D[customer_id]["type"] == "SITE_VISIT") / 52
    a = total_amount * visits_per_week
    t = count_weeks( min([x for x in D[customer_id]["event_time"]]),
                     max([x for x in D[customer_id]["event_time"]]) )
    """
    LTVs = []
    for customer_id in D:

        # VISITS PER WEEK
        # If no SITE_VISIT events exist but there are customer orders,
        # possibly due to corrupt data, interpret ORDER events as visits for backup
        vkey = visit_key if visit_key in [r['type'] for r in D[customer_id]] else 'ORDER'
        visits_date_list = [r[date_key] for r in D[customer_id] if r['type'] == vkey]
        if visits_date_list and 'ORDER' in [r['type'] for r in D[customer_id]]:
            active_weeks = count_weeks(min(visits_date_list), max(visits_date_list))
            visits_num = float(len(visits_date_list))
            # Visits per week = Total # of visits / weeks customer activity
            visits_p_week = visits_num / active_weeks

            # CUSTOMER EXPENDITURE PER VISIT
            order_data = [ (r['key'], r['verb'], r['event_time'], float(r[total_amount_key].split()[0]))
                           for r in D[customer_id] if r['type'] == order_key ]
            order_amounts_by_id = {}
            # Check for order updates
            for k, verb, ev_dt, amount in order_data:
                if k not in order_amounts_by_id:
                    order_amounts_by_id[k] = (ev_dt, amount)
                else:
                    if ev_dt > order_amounts_by_id[k][0]:
                        # Replace amount if newer update exists
                        order_amounts_by_id[k] = (ev_dt, amount)
            total_order_amounts = sum([order_amounts_by_id[k][1] for k in order_amounts_by_id])
            expenditure_per_visit = float(total_order_amounts) / visits_p_week

            # LTV
            avg_cust_val_p_week = expenditure_per_visit * visits_p_week
            cust_lifespan = 10
            LTVs.append( (customer_id, 52 * avg_cust_val_p_week * cust_lifespan) )
        else:
            # No ORDER events
            LTVs.append( (customer_id, 0) )

    LTVs.sort(reverse=True, key=lambda y: y[1])
    if print_info:
        print "\nFull LTV list:"
        for ltv in LTVs:
            print "{}".format(ltv)

    return LTVs[:x]


def topXSimpleLTVCustomers(x, D, print_info=False):
    """
    New calculation based on email reply:
    But calculating the whole visits thing is redundant. You have the overall revenue, so you can simplify to:
    LTV = (average revenue / week) * (52 weeks / year) * 10 years
    LTV = (average revenue / week) * (52 weeks / year) * 10 years
    """

    LTVs = []
    for customer_id in D:

        # VISITS PER WEEK
        # If no SITE_VISIT events exist but there are customer orders,
        # possibly due to corrupt data, interpret ORDER events as visits as backup.
        vkey = visit_key if visit_key in [r['type'] for r in D[customer_id]] else 'ORDER'
        visits_dates_list = [r[date_key] for r in D[customer_id] if r['type'] == vkey]
        # Check customer record has ORDER and SITE_VISIT events
        if visits_dates_list and 'ORDER' in [r['type'] for r in D[customer_id]]:
            active_weeks = count_weeks(min(visits_dates_list), max(visits_dates_list))

            # CUSTOMER EXPENDITURE PER VISIT
            order_data = [ (r['key'], r['verb'], r['event_time'], float(r[total_amount_key].split()[0]))
                           for r in D[customer_id] if r['type'] == order_key ]
            order_amounts_by_id = {}
            # Check for order updates
            for k, verb, ev_dt, amount in order_data:
                if k not in order_amounts_by_id:
                    order_amounts_by_id[k] = (ev_dt, amount)
                else:
                    if ev_dt > order_amounts_by_id[k][0]:
                        # Replace amount if newer update exists
                        order_amounts_by_id[k] = (ev_dt, amount)
            total_order_amounts = sum([order_amounts_by_id[k][1] for k in order_amounts_by_id])
            avg_revenue_per_week = float(total_order_amounts) / active_weeks

            # LTV
            cust_lifespan = 10
            LTVs.append( (customer_id, 52 * avg_revenue_per_week * cust_lifespan) )
        else:
            # No ORDER events
            LTVs.append( (customer_id, 0) )

    LTVs.sort(reverse=True, key=lambda y: y[1])
    if print_info:
        print "\nFull LTV list:"
        for ltv in LTVs:
            print "{}".format(ltv)

    return LTVs[:x]


if __name__ == '__main__':
    customer_info = {}
    print_info = True
    file_to_data("../input/input.txt", customer_info)
    top_LTVs = topXSimpleLTVCustomers_old(10, customer_info, print_info)
    output_file = "../output/output.txt"
    write_output(output_file, top_LTVs)
    print "\nData saved in: {}".format(output_file)