cp ../.aws/config .
cp ../.aws/credentials .

docker build . --file Dockerfile --tag compilacion_202206251825
