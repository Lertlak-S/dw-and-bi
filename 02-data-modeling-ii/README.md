# Building a Data Modeling with Cassandra (NoSQL)

1. ทำความเข้าใจความสัมพันธ์ของข้อมูลจากไฟล์ .json
2. สร้าง Data Model ด้วย Cassandra ซึ่งเป็น NoSQL Database
3. ไฟล์ etl.py มีการดำเนินการ ดังนี้
    - สร้าง Keyspace และ Table (โดยจะมีการ Drop Table ก่อน หากมี Table นั้นอยู่แล้ว)
    - จัดการข้อมูลที่ได้จากไฟล์ .json เข้าสู่ Table ใน Database
4. ทำการตรวจสอบข้อมูลใน Database โดย cqlsh (CQL shell)

### การสร้าง Table ดังนี้

1. Table: events
```python
    CREATE TABLE IF NOT EXISTS events
    (
        id text,
        type text,
        actor_id text,
        actor_login text,
        repo_id text,
        repo_name text,
        created_at timestamp,
        public boolean,
        PRIMARY KEY (
            id,
            type
        )
    )
```

### โดยสามารถ query ข้อมูลด้วย CQL Command

```sh
select * from github_events.events;
```

### ได้ตัวอย่างข้อมูลดังนี้
![Alt text](image/image.png)

# Instruction
### เข้าไปที่ folder ของไฟล์ด้วยคำสั่ง

```sh
$ cd 02-data-modeling-ii
```

### Install cqlsh package

```sh
$ pip install cqlsh
```

### Running Cassandra

```sh
$ docker-compose up
```

### Running Python Scripts
New Terminal and run:
```sh
$ python etl.py
```

### Cassandra command-line interface
```sh
$ cqlsh
```