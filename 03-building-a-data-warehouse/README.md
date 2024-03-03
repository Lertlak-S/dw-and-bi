# Building an ETL Pipeline for a Cloud Data Warehouse (Google BigQuery)

1. ทำความเข้าใจความสัมพันธ์ของข้อมูลจากไฟล์ .json
2. เตรียม Project GCP และ Credentials บน BigQuery เพื่อใช้สำหรับการ ETL
3. ทำ ETL โดยอ่าน Data Source จากไฟล์ JSON ตาม Schema และ Format ที่เราได้กำหนดไว้และเขียนข้อมูลลงไฟล์ CSV
4. และ อ่านข้อมูลไฟล์ CSV และโหลดขึ้นไปยัง BigQuery
5. มีการแสดงไฟล์ที่เป็น Data Source ทั้งหมด
6. มีการแสดงจำนวน Rows และ Columns ของแต่ละ Tables ที่ทำการโหลดข้อมูลขึ้น BigQuery

### Data Model 3 Table ดังนี้
1. actors (id, login, url)
2. repo (id, name)
3. events (id, type, actor_id, repo_id, created_at)

# Instruction
### เข้าไปที่ folder ของไฟล์ด้วยคำสั่ง
```sh
$ cd 03-building-a-data-warehouse
```

### สร้าง Environment
```sh
$ python -m venv env
```
```sh
$ source env/bin/activate
```

### เตรียมไฟล์สำหรับ Install Library ใน folder 03-building-a-data-warehouse ชื่อ requirements.txt
```sh
cachetools==5.3.2
certifi==2024.2.2
charset-normalizer==3.3.2
google-api-core==2.17.1
google-auth==2.28.1
google-cloud-bigquery==3.17.2
google-cloud-core==2.4.1
google-crc32c==1.5.0
google-resumable-media==2.7.0
googleapis-common-protos==1.62.0
idna==3.6
numpy==1.23.2
packaging==23.2
protobuf==4.25.3
psycopg2==2.9.3
pyasn1==0.5.1
pyasn1-modules==0.3.0
python-dateutil==2.8.2
pytz==2022.2.1
requests==2.31.0
rsa==4.9
six==1.16.0
urllib3==2.2.1
```

### Install Library ที่เกี่ยวข้อง
```sh
$ pip install -r requirements.txt
```

### ทำ ETL จาก Data Source ไฟล์ JSON ขึ้น Cloud Data Warehouse (Google BigQuery)
```sh
$ python etl.py
```