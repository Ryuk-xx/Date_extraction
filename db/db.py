import psycopg2
from config.config import load_config
import logging

logger = logging.getLogger("DateExtractor")

config = load_config()


class Database_logs:
    def __init__(self):
        self.host = config['database_logs']["host"]
        self.dbname = config['database_logs']["database"]
        self.user = config['database_logs']["user"]
        self.password = config['database_logs']["password"]
        self.port = config['database_logs']["port"]
        self.schema = config['database_logs']["schema"]
        self.table = config['database_logs']["log_table"]
        self.conn, self.cursor = self.connect()
    
    def connect(self):
        try:
            conn = psycopg2.connect(
                host=self.host,
                database=self.dbname,
                user=self.user,
                password=self.password,
                port=self.port
            )
            cursor = conn.cursor()
            logger.info(f"✅ DB {self.dbname} connected.")
            return conn, cursor
        except Exception as e:
            logger.info(f"❌ DB {self.dbname} connect failed", e)
            return None, None

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info(f"🔒 DB {self.dbname} close!")
    
    def create_table_logs(self):

        try:
            self.conn, self.cur = self.connect()
            # Kiểm tra schema tồn tại
            self.cur.execute("""
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.schemata 
                    WHERE schema_name = %s
                );
            """, (self.schema,))
            schema_exists = self.cur.fetchone()[0]
            if not schema_exists:
                # Tạo schema nếu chưa tồn tại
                self.cur.execute(f"CREATE SCHEMA {self.schema};")
                self.connector.commit()
                logger.info(f"Schema {self.schema} created successfully")
            # Kiểm tra bảng tồn tại
            self.cur.execute("""
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = %s 
                    AND table_name = %s
                );
            """, (self.schema, self.table))
            
            table_exists = self.cur.fetchone()[0]
            
            if not table_exists:
                create_table_query = f"""
                CREATE TABLE IF NOT EXISTS {self.schema}.{self.table} (
                    id SERIAL PRIMARY KEY,
                    file_path VARCHAR(500),
                    request_time TIMESTAMP,
                    run_time VARCHAR(50),
                    status_code INTEGER,
                    output TEXT,
                    extracted_date VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
                self.cur.execute(create_table_query)
                self.conn.commit()
                logger.info(f"Table {self.schema}.{self.table} created successfully")
            else:
                logger.info(f"Table {self.schema}.{self.table} already exists")
        except Exception as e:
            logger.error(f"Error in create_table: {e}")
        finally:
            self.close()


    def save_logs(self,file_path, request_time, run_time, status_code, output,
                    extracted_date=None, paddle_time=None, hand_cls_time=None,
                    hand_rec_time=None):

        # Insert data
        insert_query = f"""
        INSERT INTO {self.schema}.{self.table}
        (file_path, request_time, run_time, status_code, output, 
         extracted_date)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        try:
            self.conn, self.cur = self.connect()
            self.cur.execute(insert_query, (
            file_path,
            request_time,
            run_time,
            status_code,
            output,
            extracted_date if extracted_date else None,
            paddle_time if paddle_time else 'N/A',
            hand_cls_time if hand_cls_time else 'N/A',
            hand_rec_time if hand_rec_time else 'N/A'
            ))
            self.conn.commit()
            logger.info("Successfully saved log to PostgreSQL")

        except Exception as e:
            logger.error(f"Error saving to PostgreSQL: {str(e)}")
            self.conn.rollback()
        finally:
            self.close()
