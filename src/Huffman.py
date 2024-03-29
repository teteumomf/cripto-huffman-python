# Matheus de Oliveira Marques Figueredo
# -*- coding: utf-8 -*-

import os
import marshal
import cPickle
import array
import new
from fileinput import filename

                
class HuffmanNode(object):
    recurPrint = False
    def __init__(self, ch=None, fq=None, lnode=None, rnode=None, parent=None):
        self.L = lnode
        self.R = rnode
        self.p = parent
        self.c = ch
        self.fq = fq
        
    def __repr__(self):
        if HuffmanNode.recurPrint:
            lnode = self.L if self.L else '#'  
            rnode = self.R if self.R else '#'        
            return ''.join( ('(%s:%d)'%(self.c, self.fq), str(lnode), str(rnode) ) )
        else:
            return '(%s:%d)'%(self.c, self.fq)
    
    def __cmp__(self, other):
        if not isinstance(other, HuffmanNode):
            return super(HuffmanNode, self).__cmp__(other)
        return cmp(self.fq, other.fq)

def _pop_first_two_nodes(nodes):
    if len(nodes)>1:
        first=nodes.pop(0)
        second=nodes.pop(0)
        return first, second
    else:        
        return nodes[0], None
        
def _build_tree(nodes):    
    nodes.sort()
    while(True):
        first, second = _pop_first_two_nodes(nodes)
        if not second:
            return first
        parent = HuffmanNode(lnode=first, rnode=second, fq=first.fq+second.fq)
        first.p = parent
        second.p = parent
        nodes.insert(0, parent)
        nodes.sort()

def _gen_huffman_code(node, dict_codes, buffer_stack=[]):
    if not node.L and not node.R:
        dict_codes[node.c] = ''.join(buffer_stack)
        return
    buffer_stack.append('0')
    _gen_huffman_code(node.L, dict_codes, buffer_stack)
    buffer_stack.pop()
    
    buffer_stack.append('1')
    _gen_huffman_code(node.R, dict_codes, buffer_stack)
    buffer_stack.pop()

def _cal_freq(long_str):
    from collections import defaultdict
    d = defaultdict(int)
    for c in long_str:
        d[c] += 1
    return d

MAX_BITS = 8

class Encoder(object):
    def __init__(self, filename_or_long_str=None):
        if filename_or_long_str:
            if os.path.exists(filename_or_long_str):
                self.encode(filename_or_long_str)
            else:
                print '[Encoder] pega  \'%s\' como uma string para codificar. '\
                      % filename_or_long_str
                self.long_str = filename_or_long_str

    def __get_long_str(self):
        return self._long_str
    def __set_long_str(self, s):
        self._long_str = s
        if s:
            self.root = self._get_tree_root()
            self.code_map = self._get_code_map()
            self.array_codes, self.code_length = self._encode()
    long_str = property(__get_long_str, __set_long_str)
    
    def _get_tree_root(self):
        d = _cal_freq(self.long_str)
        return _build_tree(
            [HuffmanNode(ch=ch, fq=int(fq)) for ch, fq in d.iteritems()]
            )

    def _get_code_map(self):
        a_dict={}
        _gen_huffman_code(self.root, a_dict)
        return a_dict
        
    def _encode(self):
        #PARA CRIAR UM ARQUIVO COM A ARVORE BINARIA QUE ELE CONSTROI PARA O ARQUIVO
        # RETIRE OS 3 '#' DESSE METODO
        array_codes = array.array('B')
        code_length = 0
        buff, length = 0, 0
        #arq = open('ArvoreUSADA.txt', 'w')
        for ch in self.long_str:
            code = self.code_map[ch]
            #arq.write(code + '\n')
            for bit in list(code):
                if bit=='1':
                    buff = (buff << 1) | 0x01
                else: 
                    buff = (buff << 1)
                length += 1
                if length == MAX_BITS:
                    array_codes.extend([buff])
                    buff, length = 0, 0

            code_length += len(code)
        #arq.close()    
        if length != 0:
            array_codes.extend([buff << (MAX_BITS-length)])

        return array_codes, code_length

    def encode(self, filename):
        fp = open(filename, 'rb')
        self.long_str = fp.read()
        tamanho = fp.tell()
        print 'Tamanho do arquivo original: ',tamanho
        fp.close()

    def write(self, filename):
        if self._long_str:
            fcompressed = open(filename, 'wb')           
            marshal.dump(
                (cPickle.dumps(self.root), self.code_length, self.array_codes),
                fcompressed)
            tamanho2 = fcompressed.tell()
            print 'Tamanho arquivo comprimido: ', tamanho2
            fcompressed.close()
        else:
            print "Você não inseriu o nome correto."

class Decoder(object):
    def __init__(self, filename_or_raw_str=None):
        if filename_or_raw_str:
            if os.path.exists(filename_or_raw_str):
                filename = filename_or_raw_str
                self.read(filename)            
            else:
                print '[Decoder] transforma \'%s\' para string' % filename_or_raw_str
                raw_string = filename_or_raw_str
                unpickled_root, length, array_codes = marshal.loads(raw_string)
                self.root = cPickle.loads(unpickled_root)
                self.code_length = length        
                self.array_codes = array.array('B', array_codes)

    def _decode(self):
        string_buf = []
        total_length = 0    
        node = self.root
        for code in self.array_codes:
            buf_length = 0
            while (buf_length < MAX_BITS and total_length != self.code_length):
                buf_length += 1
                total_length += 1            
                if code >> (MAX_BITS - buf_length) & 1:
                    node = node.R
                    if node.c:
                        string_buf.append(node.c)
                        node = self.root
                else:
                    node = node.L
                    if node.c:
                        string_buf.append(node.c)
                        node = self.root

        return ''.join(string_buf)        

    def read(self, filename):
        fp = open(filename, 'rb')
        unpickled_root, length, array_codes = marshal.load(fp)       
        self.root = cPickle.loads(unpickled_root)
        self.code_length = length        
        self.array_codes = array.array('B', array_codes)
        fp.close()

    def decode_as(self, filename):
        decoded = self._decode()
        fout = open(filename, 'wb')
        fout.write(decoded)
        fout.close()


if __name__=='__main__':
    
    s = 0
    while s != 3: 
        r = input("Digite 1 para COMPRIMIR ou 2 para DESCOMPRIMIR ou 3 para SAIR: ")   
        if r == 1:
            s = raw_input("Digite o nome do arquivo que quer comprimir, EX: BibliaSagrada\nNAO PRECISA COLOCAR O .txt\nDigite:")
            nome = s
            enc = Encoder(nome + '.txt')
            enc.write(nome + 'Compressed.txt')
            print '\n\nPronto. Seu arquivo comprimido foi salvo com o nome de: ' + nome + 'Compressed.txt\n'
        elif r == 2:
            s = raw_input("Digite o nome do arquivo para descomprimir. \nLembre-se de digitar o NOME ORIGINAL DO ARQUIVO EX: BibliaSagrada\nNAO PRECISA COLOCAR O .txt\nDigite:")
            nome = s
            dec = Decoder(s + 'Compressed.txt')
            dec.decode_as(nome + 'Descompressed.txt')
            print '\n\nPronto. Seu arquivo comprimido foi salvo com o nome de: ' + nome + 'Descompressed.txt\n'
        else:
            print 'Obrigado.'  
            s = 3
