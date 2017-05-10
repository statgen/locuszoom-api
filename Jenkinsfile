pipeline {
  agent any

  environment {
    PATH = "/home/linuxbrew/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
  }

  stages {
    stage('preclean') {
      steps {
        sh 'rm -rf testenv'
        sh 'rm -f report.xml'
        sh 'rm -f FLASK_PORT'
        sh 'rm -f PID'
        sh '/data/redis/bin/redis-cli -n 3 flushdb'
      }
    }
    stage('build') {
      steps {
        sh 'python -m virtualenv --no-site-packages testenv'
        sh 'testenv/bin/pip install --cache-dir /data/pipcache/ -r requirements.txt'
        sh 'mkdir -p etc'
        sh 'cp /data/jenkins/locuszoom/config-jenkins.py etc/'
      }
    }
    stage('start-server') {
      steps {
        sh 'bin/unused_port.py > FLASK_PORT'
        sh 'bin/run_gunicorn.py jenkins --port `cat FLASK_PORT` --host "127.0.0.1" & echo $! > PID'
      }
    }
    stage('test') {
      steps {
        sh '''
          export FLASK_HOST="127.0.0.1"
          export FLASK_PORT=`cat FLASK_PORT`
          testenv/bin/pytest --pyargs portalapi --junitxml report.xml
        '''
        junit 'report.xml'
      }
    }
    stage('deploy') {
      when {
        branch 'dev'
      }

      steps {
        echo 'Deployment currently not implemented'
      }
    }
  }
  post {
    always {
      sh '[[ -f "PID" ]] && kill `cat PID`'
    }
  }
}
