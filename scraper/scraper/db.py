import psycopg2

def get_db_connection():
    ## Connection Details
    database = 'defaultdb'
    hostname = 'asicdb-asicdb.d.aivencloud.com'
    username = 'avnadmin'
    password = 'AVNS_NIa2cuRNNTTQnwzSN9J'
    port = '11632'
    
    try:
        ## Connect to database
        connection = psycopg2.connect(host=hostname,user=username, password=password, dbname=database, port=port)
        ## Create cursor, used to execute commands
        cur = connection.cursor()
        ## Create notices table if none exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS notices(
                acn VARCHAR(9) PRIMARY KEY, 
                name VARCHAR(200),
                note_date VARCHAR(10)
            )
        """)
        return connection
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    return False

global db
db = get_db_connection()