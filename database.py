import pymysql
import datetime
from db_login import db_info


class DB:
    def __init__(self):
        try:
            self.conn = pymysql.connect(**db_info)
            print("db connection successed")
            self.cur = self.conn.cursor()
        except Exception as e:
            print(f'db connection failed: {e}')
        
    def search_item(self, item):
        try:
            # 아이템을 검색하는 쿼리 (대소문자 구분 없이 검색)
            query = "SELECT location FROM ItemLocation WHERE TRIM(name) = %s"
            self.cur.execute(query, (item, ))  # LIKE 쿼리 사용
            result = self.cur.fetchall()

            if result:
                locations = list(set(row[0] for row in result))  # 여러 개의 location이 있을 수 있음
                print(f"Item '{item}' found at locations: {locations}")
                return locations
            else:
                print(f"Item '{item}' not found.")
                return None
        except Exception as e:
            print(f"Error in search_item: {e}")
            return None
        
    def search_location(self, location):
        try:
            if location == '*':
                # 모든 location 값을 가져오는 쿼리
                query = "SELECT DISTINCT location FROM ItemLocation"
                self.cur.execute(query)
                result = self.cur.fetchall()

                if result:
                    return [row[0] for row in result]  # 중복되지 않은 location 리스트 반환
                else:
                    print(f"No locations found.")
                    return None
            else:
                # 위치에 해당하는 아이템을 검색하는 쿼리
                query = "SELECT name FROM ItemLocation WHERE location = %s"
                self.cur.execute(query, (location,))
                result = self.cur.fetchall()

                if result:
                    items = [row[0] for row in result]  # 여러 개의 item이 있을 수 있음
                    print(f"Items found at location '{location}': {items}")
                    return items
                else:
                    print(f"No items found at location '{location}'.")
                    return None
        except Exception as e:
            print(f"Error in search_location: {e}")
            return None


    def add_item(self, location, item):
        try:
            # 이미 해당 location과 item이 존재하는지 확인
            query = "SELECT quantity FROM ItemLocation WHERE location = %s AND name = %s"
            self.cur.execute(query, (location, item))
            result = self.cur.fetchone()

            if result:  # 이미 아이템이 존재하는 경우, quantity를 업데이트
                new_quantity = result[0] + 1
                update_query = "UPDATE ItemLocation SET quantity = %s WHERE location = %s AND name = %s"
                self.cur.execute(update_query, (new_quantity, location, item))
                self.conn.commit()
                print(f"Item '{item}' at location '{location}' updated with new quantity {new_quantity}.")
            else:  # 새로 추가하는 경우
                insert_query = "INSERT INTO ItemLocation (location, name, quantity) VALUES (%s, %s, %s)"
                self.cur.execute(insert_query, (location, item, 1))  # 기본 quantity 1
                self.conn.commit()
                print(f"Item '{item}' added at location '{location}' with quantity 1.")
        except Exception as e:
            self.conn.rollback()  # 실패시 롤백
            print(f"Error in add_item: {e}")
            return None
        
    def remove_item(self, item):
        try:
            # 해당 아이템의 quantity를 가져옴
            query = "SELECT location, quantity FROM ItemLocation WHERE name = %s"
            self.cur.execute(query, (item,))
            results = self.cur.fetchall()

            if results:
                for location, quantity in results:
                    if quantity > 1:  # quantity가 1보다 크면, 수량을 하나 줄임
                        new_quantity = quantity - 1
                        update_query = "UPDATE ItemLocation SET quantity = %s WHERE location = %s AND name = %s"
                        self.cur.execute(update_query, (new_quantity, location, item))
                        print(f"Decreased quantity of '{item}' at location '{location}' to {new_quantity}.")
                        self.conn.commit()
                        return 2
                    else:  # quantity가 1이면, 해당 항목 삭제
                        delete_query = "DELETE FROM ItemLocation WHERE location = %s AND name = %s"
                        self.cur.execute(delete_query, (location, item))
                        print(f"Item '{item}' removed from location '{location}'.")
                        self.conn.commit()
                        return 1
                
            else:
                print(f"Item '{item}' not found to remove.")
                return 0

        except Exception as e:
            self.conn.rollback()  # 실패시 롤백
            print(f"Error in remove_item: {e}")
            return None
        

    def log_usage(self, name):
        try:
            query_get_id = "SELECT id FROM TeamMember WHERE name = %s"
            self.cur.execute(query_get_id, (name,))
            result = self.cur.fetchone()
    
            if not result:
                return None
    
            member_id = result[0]
    
            query_history = """
                SELECT usage_num, start_time, stop_time
                FROM UsageHistory
                WHERE id = %s
                ORDER BY usage_num DESC LIMIT 1
            """
            self.cur.execute(query_history, (member_id,))
            history_result = self.cur.fetchone()
    
            now = datetime.datetime.now()
            start_time = now.strftime('%Y-%m-%d %H:%M:%S')
            usage_date = now.date()
    
            if history_result:
                last_usage_num, last_start, last_stop = history_result
    
                if last_stop is None:
                    stop_time = start_time
                    update_query = "UPDATE UsageHistory SET stop_time = %s WHERE usage_num = %s"
                    self.cur.execute(update_query, (stop_time, last_usage_num))
                    self.conn.commit()
                else:
                    insert_query = """
                        INSERT INTO UsageHistory (id, name, usage_date, start_time)
                        VALUES (%s, %s, %s, %s)
                    """
                    self.cur.execute(insert_query, (member_id, name, usage_date, start_time))
                    self.conn.commit()
            else:
                insert_query = """
                    INSERT INTO UsageHistory (id, name, usage_date, start_time)
                    VALUES (%s, %s, %s, %s)
                """
                self.cur.execute(insert_query, (member_id, name, usage_date, start_time))
                self.conn.commit()
    
        except Exception as e:
            self.conn.rollback()
            print(f"Error in log_usage: {e}")
            return None
    

    def search_by_id(self, card_id):
        try:
            query = "SELECT name FROM TeamMember WHERE card_id=%s"
            self.cur.execute(query, (card_id, ))
            result = self.cur.fetchone()

            if result:
                user = result[0]
                print(user)
                return user
            else:
                print("no user.")
                return None
        
        except:
            print(f"{card_id} not found.")
            return None
        
        
    def record_emergency(self, name):
        try:
            now = datetime.datetime.now()
            try:
                query = "SELECT id FROM TeamMember WHERE name=%s"
                self.cur.execute(query, (name, ))
                result = self.cur.fetchone()
            except Exception as  e:
                print(e)
                return None

            id = result[0]
            
            occurred_at = now.strftime('%Y-%m-%d %H:%M:%S')
            query = "INSERT INTO EmergencyRecord (id, name, occurred_at) VALUES(%s, %s, %s)"
            self.cur.execute(query, (id, name, occurred_at))
            self.conn.commit()
            print(f"{name} upload db (emergency)")
        
        except Exception as e:
            print(e)
            return None
        
        
    def __del__(self):
        # 객체 삭제 시 DB 연결 닫기
        self.cur.close()
        self.conn.close()
        print("DB connection closed.")