"""
Description:
Helper script used to create artificial data to validate main program.
This is in no way required to verify or run main program.
If it is desired to run this program, Faker was installed pip as: "pip install faker"
"""

import random
import string
from datetime import datetime
from faker import Faker


def random_id(n):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in xrange(n))

def date_str(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def make_data(n_customers, n_events, path):
    fake = Faker()
    first_iter = True
    event_type_list = ['SITE_VISIT', 'IMAGE', 'ORDER', 'CUSTOMER']

    with open(path, 'w') as f:

        for _ in xrange(n_customers):
            cust_id = random_id(12)
            # {"type":     "CUSTOMER", "verb":"NEW", "key":"96f55c7d8f42", "last_name":"Smith",
            # "event_time":"2017-01-06T12:46:46.384Z", "adr_city":"Middletown", "adr_state":"AK"},
            new_cust_dt = fake.date_time_this_decade()
            custmer_entry = { 'type': 'CUSTOMER', 'verb': 'NEW', 'key': cust_id, 'last_name': fake.last_name(),
                'event_time': date_str(new_cust_dt), 'adr_city': fake.city(), 'adr_state': fake.state() }

            # Write customer entry
            if first_iter:
                f.write('[' + str(custmer_entry))
                first_iter = False
            else:
                f.write(',\n' + str(custmer_entry))

            print "Customer entry #{}:\n{}".format(_, custmer_entry)

            # Create events
            for i in xrange(random.randint(0,n_events)):
                event_date = fake.date_time_this_decade()
                event_type = event_type_list[random.randint(0,len(event_type_list)-1)]

                if event_type == 'SITE_VISIT':
                    event = { 'type': event_type, 'verb': 'NEW', 'key': random_id(15),
                              'event_time': date_str(event_date), 'customer_id': cust_id }

                elif event_type == 'IMAGE':
                    event = { 'type': event_type, 'verb': 'UPLOAD', 'key': random_id(12),
                              'event_time': date_str(event_date), 'customer_id': cust_id }

                elif event_type == 'ORDER':
                    order_id = random_id(8)
                    event = { 'type': event_type, 'verb': 'NEW', 'key': order_id,
                              'event_time': date_str(event_date), 'customer_id': cust_id,
                              'total_amount': "{:.2f} USD".format(random.uniform(4, 500))}
                    f.write(',\n' + str(event))
                    print "\tEvent #{}:\n\t{}".format(i, event)
                    # Randomly update orders 0-2 times
                    for upd in xrange(random.randint(0,2)):
                        event = {'type':event_type, 'verb':'UPDATE', 'key':order_id, 'customer_id':cust_id,
                                 'event_time':  date_str(fake.date_time_between_dates(event_date, datetime.now())),
                                 'total_amount':"{:.2f} USD".format(random.uniform(4, 500))}
                        f.write(',\n' + str(event))
                        print "\t > Update #{}:\n\t   {}".format(upd, event)

                elif event_type == 'CUSTOMER':
                    event = { 'type': event_type, 'verb': 'UPDATE', 'key': cust_id, 'adr_state': fake.state(),
                              'event_time': date_str(fake.date_time_between_dates(new_cust_dt, datetime.now())) }

                print "\tEvent #{}:\n\t{}".format(i, event)
                if event_type != 'ORDER':
                    f.write(',\n' + str(event))

        f.write(']')
        print "\nCreated ({}) customer entries in file: {}".format(n_customers, path)


if __name__ == '__main__':
    new_customers = 100
    max_random_events = 12
    fpath = "../input/input.txt"
    make_data(new_customers, max_random_events, fpath)