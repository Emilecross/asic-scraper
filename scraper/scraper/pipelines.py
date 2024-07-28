from scraper.db import db
from scrapy.mail import MailSender

class PSQLPipeline:
    def __init__(self):
        # Grab the db connection and cursor
        self.connection = db
        self.cur = self.connection.cursor()
        self.mailer = MailSender(smtphost='smtp.gmail.com',
                                 smtpport=587,
                                 mailfrom='asicdb@gmail.com',
                                 smtpuser='asicdb@gmail.com',
                                 smtppass='sygusocuvqgfkrbr',
                                 smtptls=True,
                                 smtpssl=False,)
        
    def process_item(self, notice, spider):
        # Secondary check if already existing notice in db
        self.cur.execute("select * from notices where acn = %s", (notice['acn'],))
        result = self.cur.fetchone()

        # if it is not already in our db
        if not result:
            print("Inserted {}, ACN:{}, {} into db".format(notice['note_date'], 
                                                           notice['acn'], 
                                                           notice['name']))

            # Insert into the db
            self.cur.execute(""" insert into notices (acn, name, note_date) values (%s,%s,%s)""", (
                notice["acn"],
                notice["name"],
                notice["note_date"],
            ))
            # Commit change (performance can be improved via bulk commits)
            self.connection.commit()

            # send email, currently sends to self
            self.mailer.send(to=['asicdb@gmail.com'], 
                             subject='New Liquidation Notice: ACN {}'.format(notice['acn']),
                             body='Company Name: {}\nACN:{}\nWas just marked as entering liquidation on {}'.format(
                                 notice["name"], 
                                 notice["acn"], 
                                 notice["note_date"])
                             )
        return notice

    
    def close_spider(self, spider):
        ## Close cursor & connection to database 
        self.cur.close()
        self.connection.close()
