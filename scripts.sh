# uruchomienie dockera z bazą danych nazwaną kk_db i użytkownikiem root z hasłem root
# do uruchomienia na początku przed rozpoczęniem pracy z aplikacją
docker run --name mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=kk_db -d mysql:9.3.0

# migracja do mysql
python manage.py migrate