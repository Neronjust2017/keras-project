from comet_ml import experiment
from data_loader.uts_classification_data_loader import UtsClassificationDataLoader
from models.uts_classification_model import UtsClassificationModel
from trainers.uts_classification_trainer import UtsClassificationTrainer
from evaluater.uts_classification_evaluater import UtsClassificationEvaluater
from utils.config import process_config_UtsClassification
from utils.dirs import create_dirs
from utils.utils import get_args
import os
import time
import nni
import logging

LOG = logging.getLogger('main_classification')

from utils.config import get_config_from_json

def process_config_UtsClassification_bayes_optimization(json_file,learning_rate,model_name, num_epochs=50, batch_size=16 ):
    config, _ = get_config_from_json(json_file)

    config.model.name = model_name
    config.model.learning_rate = learning_rate
    config.trainer.num_epochs = num_epochs
    config.trainer.batch_size = batch_size

    config.callbacks.tensorboard_log_dir = os.path.join("experiments",time.strftime("%Y-%m-%d/", time.localtime()),
                                                        config.exp.name, config.dataset.name,
                                                        config.model.name, "tensorboard_logs",
                                                        "lr=%s,epoch=%s,batch=%s" % (
                                                            config.model.learning_rate, config.trainer.num_epochs,
                                                            config.trainer.batch_size)
                                                       )
    config.callbacks.checkpoint_dir = os.path.join("experiments", time.strftime("%Y-%m-%d/", time.localtime()),
                                                   config.exp.name, config.dataset.name,
                                                   config.model.name, "%s-%s-%s" % (
                                                   config.model.learning_rate, config.trainer.num_epochs,
                                                   config.trainer.batch_size),
                                                   "checkpoints/")
    config.log_dir = os.path.join("experiments", time.strftime("%Y-%m-%d/", time.localtime()),
                                            config.exp.name, config.dataset.name,
                                            config.model.name, "%s-%s-%s" % (
                                            config.model.learning_rate, config.trainer.num_epochs,
                                            config.trainer.batch_size),
                                            "training_logs/")
    config.result_dir = os.path.join("experiments", time.strftime("%Y-%m-%d/", time.localtime()),
                                               config.exp.name, config.dataset.name,
                                               config.model.name, "%s-%s-%s" % (
                                                   config.model.learning_rate, config.trainer.num_epochs,
                                                   config.trainer.batch_size),
                                               "result/")
    return config

def generate_default_params():
    '''
    Generate default hyper parameters
    '''
    return {
        'learning_rate': 0.001,
        'model_name':'mlp'
    }

def main():
    import os
    print(os.getcwd())
    os.chdir('../../..')
    print(os.getcwd())

    os.environ['CUDA_VISIBLE_DEVICES'] = '3'
    try:

        RECEIVED_PARAMS = nni.get_next_parameter()

        LOG.debug(RECEIVED_PARAMS)

        PARAMS = generate_default_params()

        PARAMS.update(RECEIVED_PARAMS)

        args = get_args()

        print(PARAMS['learning_rate'])

        config = process_config_UtsClassification_bayes_optimization(args.config,PARAMS['learning_rate'],PARAMS['model_name'])
        # except:
        #     print("missing or invalid arguments")
        #     exit(0)

        # create the experiments dirs
        create_dirs([config.callbacks.tensorboard_log_dir, config.callbacks.checkpoint_dir,
                     config.log_dir, config.result_dir])

        print('Create the data generator.')
        data_loader = UtsClassificationDataLoader(config)

        print('Create the model.')

        model = UtsClassificationModel(config, data_loader.get_inputshape(), data_loader.get_nbclasses())

        print('Create the trainer')
        trainer = UtsClassificationTrainer(model.model, data_loader.get_train_data(), config)

        print('Start training the model.')
        trainer.train()

        print('Create the evaluater.')
        evaluater = UtsClassificationEvaluater(trainer.best_model, data_loader.get_test_data(), data_loader.get_nbclasses(),
                                               config)

        print('Start evaluating the model.')
        evaluater.evluate()
        nni.report_final_result(evaluater.f1)

        print('done')

    except Exception as e:
        LOG.exception(e)
        raise

if __name__ == '__main__':
    main()
