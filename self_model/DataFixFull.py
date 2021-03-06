#!/usr/bin/env python
# coding=utf-8

import os
import random
import numpy as np
from Utils import extract_feature
from keras.preprocessing.sequence import pad_sequences
class DataConfig():
    base_dir='/data/dataset/'
    data_names=['st-cmds','thchs30','primewords','aishell']
    data_dirs={name:'/data/dataset/'+name+'/' for name in data_names}
    wav2py_paths={}
    types=['train','test','dev']
    for type in types:
        temp={}
        for name in ['syllabel','wav']:
            temp[name]=type+'.'+name+'.txt' if name!='wav' else type+'.'+name+'.lst'
        wav2py_paths[type]=temp
    dict_dir=base_dir+'dict/'
    py2id_dict=dict_dir+'py2id_dict.txt'
    hz2id_dict=dict_dir+'hz2id_dict.txt'
    py2hz_dict=dict_dir+'py2hz_dict.txt'
    py2hz_dir=base_dir+'pinyin2hanzi/'

class ConfigSpeech(DataConfig):
    output_size=1472
    label_len=50
    audio_len=2000
    audio_feature_len=200
    epochs=10
    save_step=1000
    batch_size=16
    dev_num=10
    train_num=100
    model_dir='models/speech_model/fixfull/'
    model_name='speech.model'
    model_path=model_dir+model_name
    log_dir='log/'
    log_name='speechfixfull.txt'
    log_path=log_dir+log_name

class DataSpeech(ConfigSpeech):
    def __init__(self):
        super(DataSpeech,self).__init__()
        self.create_dict()
        self.create_wav2py()
    def create_wav2py(self):
        self.wav2py={}
        self.batch_num={}
        for _type,path in self.wav2py_paths.items():
            self.wav2py[_type]={}
            start_num=0
            for name,data_dir in self.data_dirs.items():
                id2wav={}
                id2py={}
                with open(data_dir+self.wav2py_paths[_type]['wav'],'r',encoding='utf-8') as file:
                    for line in file:
                        idx,path=line.strip('\n').strip().split(' ')
                        id2wav[idx.strip()]=self.base_dir+path.strip()
                with open(data_dir+self.wav2py_paths[_type]['syllabel'],'r',encoding='utf-8') as file:
                    for line in file:
                        ws=line.strip('\n').strip().split(' ')
                        idx,pys=ws[0],ws[1:]
                        id2py[idx.strip()]=pys
                assert len(id2py)==len(id2wav)
                for idx,key in enumerate(id2py.keys()):
                    self.wav2py[_type][start_num+idx]=(id2wav[key],id2py[key])
                start_num=len(self.wav2py[_type])
            batch_num=start_num //self.batch_size
            self.batch_num[_type]=batch_num if start_num%self.batch_size==0 else batch_num+1


    def create_batch(self,flag='train',shuffle=True):
        data_num=len(self.wav2py[flag])
        idxs=list(range(data_num))
        if shuffle:
            random.shuffle(idxs)
        wavs=[]
        labels=[]
        for i,idx in enumerate(idxs):
            wav_path,pys=self.wav2py[flag][idx]
            fbank=extract_feature(wav_path)
            label=np.array([self.py2id[py] for py in pys])
            while((fbank.shape[0]>=self.audio_len ) or (len(label)>=self.label_len)):
                temp=random.randint(len(idxs)//4,len(idxs)//2)
                wav_path,pys=self.wav2py[flag][temp]
                fbank=extract_feature(wav_path)
                label=np.array([self.py2id[py] for py in pys],dtype=np.int32)

            assert len(wavs)==len(labels)
            if len(wavs)==self.batch_size:
                the_inputs,input_length=self.wav_padding(wavs)
                the_labels,label_length=self.label_padding(labels)
                inputs=[the_inputs,the_labels,input_length,label_length]
                outputs=np.zeros([self.batch_size,1],dtype=np.float32)
                yield inputs,outputs
                wavs,labels=[],[]
            wavs.append(fbank)
            labels.append(label)
        if len(wavs)!=0:
            the_inputs,input_length=self.wav_padding(wavs)
            the_labels,label_length=self.label_padding(labels)
            inputs=[the_inputs,the_labels,input_length,label_length]
            outputs=np.zeros([len(wavs),1],dtype=np.float32)
            yield inputs,outputs
    def wav_padding(self,wavs):
        wav_lens=[wav.shape[0] for wav in wavs]
        max_len=self.audio_len
        wav_lens=np.array([leng//8+leng%8 for leng in wav_lens],dtype=np.int32).T
        new_wavs=np.zeros((len(wavs),max_len,self.audio_feature_len,1))
        for i in range(len(wavs)):
            wav=wavs[i][:wavs[i].shape[0]//8*8,:]
            #wav=wavs[i]
            new_wavs[i,:wav.shape[0],:,:]=wav
        return new_wavs,wav_lens

    def label_padding(self,labels):
        label_lens=np.array([[label.shape[0]] for label in labels])
        max_len=self.label_len
        new_labels=np.zeros((len(labels),max_len),dtype=np.int32)
        for i in range(len(labels)):
            new_labels[i,:len(labels[i])]=labels[i]
        return new_labels,label_lens


    def create_dict(self):
        self.py2id={}
        self.id2py={}
        with open(self.py2id_dict,'r',encoding='utf-8') as file:
            for line in file:
                py,idx=line.strip('\n').strip().split('\t')
                self.py2id[py.strip()]=int(idx.strip())
                self.id2py[int(idx.strip())]=py.strip()


def main():
    data=DataSpeech()
    data_iters=data.create_batch()
    for batch in data_iters:
        x,y=batch
        print(x[0].shape,x[1].shape,x[2].shape,x[3].shape,y.shape)

if __name__=="__main__":
    main()
