node {
  if (env.BRANCH_NAME == "command"){
    properties([
      parameters([string(defaultValue: '', description: 'staging / production', name:'enviroment'),
      string(defaultValue: 'python manage.py migrate', description: "Django's Command", name:'djangocommand')])
    ])
  }
  if (env.BRANCH_NAME == 'command' && params.enviroment == ''){
    return
  }
  checkout scm
  withCredentials([usernamePassword(credentialsId: 'docker', passwordVariable: 'DOCKER_PASSWORD', usernameVariable: 'DOCKER_USERNAME')]) {
    sh("docker login -u ${env.DOCKER_USERNAME} -p ${env.DOCKER_PASSWORD} registry.aliyuncs.com")
  }
  sh("docker build -t xiaolusys:latest .")
  if (env.BRANCH_NAME == 'command'){
    if (params.enviroment == 'production'){
      withCredentials([usernamePassword(credentialsId: 'redis_production', passwordVariable: 'REDIS_AUTH', usernameVariable: 'REDIS_USER'),
        usernamePassword(credentialsId: 'mysql_production', passwordVariable: 'MYSQL_AUTH', usernameVariable: 'MYSQL_USER')]) {
        sh("docker run -e TARGET=k8s-production -e MYSQL_AUTH=${env.MYSQL_AUTH} -e REDIS_AUTH=${env.REDIS_AUTH} xiaolusys:latest ${params.djangocommand}")
      }
    } 
    if (params.enviroment == 'staging'){
      withCredentials([usernamePassword(credentialsId: 'redis', passwordVariable: 'REDIS_AUTH', usernameVariable: 'REDIS_USER'),
        usernamePassword(credentialsId: 'mysql', passwordVariable: 'MYSQL_AUTH', usernameVariable: 'MYSQL_USER')]) {
        sh("docker run -e TARGET=k8s -e MYSQL_AUTH=${env.MYSQL_AUTH} -e REDIS_AUTH=${env.REDIS_AUTH} xiaolusys:latest ${params.djangocommand}")
      }
    }
  } else {
    withCredentials([usernamePassword(credentialsId: 'redis', passwordVariable: 'REDIS_AUTH', usernameVariable: 'REDIS_USER'),
      usernamePassword(credentialsId: 'mysql', passwordVariable: 'MYSQL_AUTH', usernameVariable: 'MYSQL_USER')]) {
      sh("docker run -e TARGET=k8s -e MYSQL_AUTH=${env.MYSQL_AUTH} -e REDIS_AUTH=${env.REDIS_AUTH} xiaolusys:latest python manage.py test -t . --keepdb --exclude-tag=B --exclude-tag=C")
    }
    sh("docker tag xiaolusys:latest registry.aliyuncs.com/xiaolu-img/xiaolusys:`git rev-parse HEAD`")
    sh("docker push registry.aliyuncs.com/xiaolu-img/xiaolusys:`git rev-parse HEAD`")
  }

  if (env.BRANCH_NAME == "master") {
    stage('Deploy to kubenetes:'){
      gitCommit = sh(returnStdout: true, script: 'git rev-parse HEAD').trim()
      build job: 'xiaolusys-deployment/staging', parameters: [[$class: 'StringParameterValue', name: 'commit_id', value: gitCommit]]
    }
  }
}

