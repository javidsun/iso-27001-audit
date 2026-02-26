

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
