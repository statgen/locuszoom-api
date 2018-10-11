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
        sh 'python3 -m virtualenv --no-site-packages testenv'
        sh 'mkdir -p etc'
        sh 'cp /data/jenkins/locuszoom/config-jenkins.py etc/'
        sh 'testenv/bin/pip install --cache-dir /data/pipcache/ -e .'
        sh 'testenv/bin/pip install --cache-dir /data/pipcache/ --force-reinstall -I psycopg2'
      }
    }
    stage('test') {
      steps {
        sh '''
          export LZAPI_MODE="jenkins"
          testenv/bin/pytest --junitxml report.xml tests
        '''
      }
    }
    stage('deploy') {
      when {
        branch 'dev'
      }

      steps {
        sh '''
          export LZAPI_HOME="/home/portaldev/lzapi_dev"
          sudo -H -u lzapi /home/portaldev/lzapi_dev/bin/deploy.py dev
        '''
      }
    }
  }
  post {
    always {
      junit 'report.xml'
    }
  }
}
