#!/usr/bin/python
# -*- coding: UTF-8 -*-
import math
from make_train_test_set import *
from train import *
from cal_F1 import *
from submit import *
from clean import *
from get_actions import *


FilePath = "../JData/"
ActionFiles = ["JData_Action_201602.csv", "JData_Action_201603.csv", "JData_Action_201604.csv"]
CommentFile = "JData_Comment.csv"
ProductFile = "JData_Product.csv"
UserFile = "JData_User.csv"
ActionAllFile = ""

def run_all(ifonline):
    flag=False
    train_start_date_str = ''
    train_end_date_str = ''
    label_start_date_str = ''
    label_end_date_str = ''
    predict_start_date_str = ''
    predict_end_date_str = ''
    predict_label_start_date_str = ''
    predict_label_end_date_str = ''
    if ifonline=='online':
        flag=True
        train_start_date_str = '2016-04-01'
        train_end_date_str = '2016-04-10'
        label_start_date_str = '2016-04-11'
        label_end_date_str = '2016-04-15'
        predict_start_date_str = '2016-04-05'
        predict_end_date_str = '2016-04-15'
        ActionAllFile = "s1_onlinecleaned_action_all.csv"
    elif ifonline=='offline':
        flag=False
        train_start_date_str = '2016-03-27'
        train_end_date_str = '2016-04-05'
        label_start_date_str = '2016-04-06'
        label_end_date_str = '2016-04-10'
        predict_start_date_str = '2016-04-01'
        predict_end_date_str = '2016-04-10'
        predict_label_start_date_str = '2016-04-11'
        predict_label_end_date_str = '2016-04-15'
        ActionAllFile = "s1_offlinecleaned_action_all.csv"
    print ifonline

    train_start_datetime = pd.to_datetime(train_start_date_str + ' 00:00:00', format='%Y-%m-%d %H:%M:%S')
    train_end_datetime = pd.to_datetime(train_end_date_str + ' 23:59:59', format='%Y-%m-%d %H:%M:%S')
    label_start_datetime = pd.to_datetime(label_start_date_str + ' 00:00:00', format='%Y-%m-%d %H:%M:%S')
    label_end_datetime = pd.to_datetime(label_end_date_str + ' 23:59:59', format='%Y-%m-%d %H:%M:%S')
    predict_start_datetime = pd.to_datetime(predict_start_date_str + ' 00:00:00', format='%Y-%m-%d %H:%M:%S')
    predict_end_datetime = pd.to_datetime(predict_end_date_str + ' 23:59:59', format='%Y-%m-%d %H:%M:%S')

    #读入action_all
    action_data=pd.read_csv(FilePath+ActionAllFile)
    action_data['time']= pd.to_datetime(action_data['time'],format='%Y-%m-%d %H:%M:%S')
    #求出action==8的set
    action_data_cate8=action_data[action_data['cate']==8]
    
    xgb_preds_file = 'xgb_preds_' + predict_start_date_str + 'to' + predict_end_date_str + '.csv'
    #feature_score_file = 'feature_score' + predict_start_date_str + 'to' + predict_end_date_str + '.csv'
    predict_real_label_file = 'real_label_'+label_start_date_str+'to'+label_end_date_str+'.csv'
    sku_fea_file = 'sku_fea_'+train_start_date_str+'to'+train_end_date_str+'.csv'
    user_fea_file = 'user_fea_'+train_start_date_str+'to'+train_end_date_str+'.csv'
    train_set_file = 'train_set_'+train_start_date_str+'to'+train_end_date_str+'.csv'
    predict_set_file = 'predict_set_' + predict_start_date_str + 'to' + predict_end_date_str + '.csv'
    if not flag:
        predict_label_start_datetime = pd.to_datetime(predict_label_start_date_str + ' 00:00:00', format='%Y-%m-%d %H:%M:%S')
        predict_label_end_datetime = pd.to_datetime(predict_label_end_date_str + ' 23:59:59', format='%Y-%m-%d %H:%M:%S')
        predict_real_label = get_labels(predict_label_start_datetime, predict_label_end_datetime,action_data_cate8)
        predict_real_label.to_csv(FilePath+predict_real_label_file, index=False)
        print 'predict_reak_label 线下真实label生成完毕'

    sku_fea = gen_sku_fea(train_start_datetime,train_end_datetime,action_data_cate8)
    sku_fea.to_csv(FilePath+sku_fea_file, index=False)
    print '商品特征生成完毕'

    user_fea = gen_user_fea(train_start_datetime,train_end_datetime,action_data)
    user_fea.to_csv(FilePath + user_fea_file, index=False)
    print '用户特征生成完毕'

    train_set=make_fea_set(sku_fea, user_fea, train_start_datetime, train_end_datetime,action_data_cate8)
    labels=get_labels(label_start_datetime,label_end_datetime,action_data_cate8)
    
    column_name_of_type4_before10 = '%s-%s-action_4' % (train_end_datetime-pd.to_timedelta('10 days'), train_end_datetime)
    #train_set=train_set[train_set[column_name_of_type4_before10]==0]
    
    train_set=pd.merge(train_set,labels,on=['user_id','sku_id'],how='left')
    train_set['label'].fillna(0, inplace=True)
    labels=train_set[['label']]
    
    train_set.drop(['user_id','sku_id','label'],axis=1,inplace=True)
    print '训练集生成完毕'
    train_set.to_csv(FilePath + train_set_file, index=False)

    predict_set = make_fea_set(sku_fea, user_fea, predict_start_datetime, predict_end_datetime,action_data_cate8)
    column_name_of_type4_before10 = '%s-%s-action_4' % (predict_end_datetime - pd.to_timedelta('10 days'), predict_end_datetime)
    #predict_set=predict_set[predict_set[column_name_of_type4_before10]==0]
    user_sku_pair_predict = predict_set[['user_id', 'sku_id']]
    predict_set.drop(['user_id', 'sku_id'], axis=1,inplace=True)
    print '预测集生成完毕'
    predict_set.to_csv(FilePath + predict_set_file, index=False)

    xgb_preds= train_and_predict(train_set,labels,user_sku_pair_predict,predict_set)
    xgb_preds.to_csv(FilePath+xgb_preds_file,index=False)
    print '预测完毕'

    if not flag:
        i = 0.0
        while i < 1:
            print i,'score,F11,F12'
            result = submit(xgb_preds, i)
            cal_F1(result, predict_real_label)
            if i<0.4:
                i += 0.1
            else:
                i += 0.01
    else:
        submitcsv = submit(xgb_preds, 0.4)
        submitcsv.to_csv(FilePath + submit_file, index=False)

if __name__ == '__main__':
    run_all('online')