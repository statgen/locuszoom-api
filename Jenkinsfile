pipeline {
  agent any

  environment {
    PATH = "/home/linuxbrew/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
  }

  /*
    FLASK_PORT = port used by flask server used for running test cases
  */

  stages {
    stage('preclean') {
      steps {
        sh 'rm -rf testenv'
        sh 'rm -f report.xml'
        sh 'rm -f FLASK_PORT'
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
        sh '''
          source testenv/bin/activate
          bin/run_gunicorn.py jenkins --port `cat FLASK_PORT` --host "127.0.0.1" &
        '''
      }
    }
    stage('test') {
      steps {
        sh '''
          export PORTALAPI_MODE="jenkins"
          export FLASK_HOST="127.0.0.1"
          export FLASK_PORT=`cat FLASK_PORT`
          testenv/bin/pytest --pyargs locuszoom.api --junitxml report.xml
        '''
      }
    }
    stage('deploy') {
      when {
        branch 'dev'
      }

      steps {
        sh '''
          export API_HOME="/home/portaldev/lzapi_dev"
          sudo -H -u lzapi /home/portaldev/lzapi_dev/bin/deploy.py dev
        '''
      }
    }
  }
  post {
    always {
      sh 'testenv/bin/python bin/kill_server.py --port `cat FLASK_PORT` --kill'
      junit 'report.xml'
    }
  }
}
