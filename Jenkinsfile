node {
  checkout scm
  withCredentials([usernamePassword(credentialsId: 'docker', passwordVariable: 'DOCKER_PASSWORD', usernameVariable: 'DOCKER_USERNAME')]) {
    sh("docker login -u ${env.DOCKER_USERNAME} -p ${env.DOCKER_PASSWORD} registry.aliyuncs.com")
  }
  sh("docker build -t xiaolusys:latest .")
  withCredentials([usernamePassword(credentialsId: 'redis', passwordVariable: 'REDIS_AUTH', usernameVariable: 'REDIS_USER')]) {
    sh("docker run -e TARGET=k8s -e REDIS_AUTH=${env.REDIS_AUTH} xiaolusys:latest python manage.py test -t . --keepdb --parallel 2 --exclude-tag=B --exclude-tag=C")
  }
  sh("docker tag xiaolusys:latest registry.aliyuncs.com/xiaolu-img/xiaolusys:`git rev-parse HEAD`")
  sh("docker push registry.aliyuncs.com/xiaolu-img/xiaolusys:`git rev-parse HEAD`")
}

