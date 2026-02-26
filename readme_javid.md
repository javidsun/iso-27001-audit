

installation venv 
```sh
  source .venv/bin/activate 
  pip install -U pip
  pip install -e ".[dev]"
```
### installation requirements.txt
```sh
    pip install -r requirements.txt
```

### docker
```shell
    docker compose down -v
```
```shell
    docker compose down
```
```shell
    docker compose up --build
```
```shell
    docker compose up
```
lista di container 
```shell
    docker ps
```
seen db without installation psql on pc
or you can install postgresql
iso-audit-db --> docker service name e container of database 
iso_user --> this is user of database create a user on database with iso_user name , is necessary for authentication on db "CREATE USER iso_user" 
iso_audit --> this is db name in posgres_db camp , so is our database name "CREATE DATABASE iso_audit"

| Nome         | Cos'è                 | A cosa serve                 |
| ------------ | --------------------- | ---------------------------- |
| iso-audit-db | Nome container Docker | Host interno per connessione |
| iso_user     | Utente PostgreSQL     | Login al DB                  |
| iso_audit    | Database PostgreSQL   | Dove stanno le tabelle       |


```shell
    docker exec -it iso-audit-db psql -U iso_user -d iso_audit
```
or 
```
    brew install postgresql
    psql -h localhost -p 5433 -U iso_user -d iso_audit
```


### git 
    
```shell
    git fetch
    git pull
```
```shell
    git rebase develop
```
```shell
    git merge feature
```
```shell
    git add .
    git commit -m "fix:message"
    git push
```
```shell
    git push --force-with-lease
```
```bash
    git switch <file_name>
```
```shell
    git switch -v <new_file_name>
```

