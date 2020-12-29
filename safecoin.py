# -*- coding: utf-8 -*-
"""
Created on Mon May  4 18:55:24 2020

@author: Keshav Bansal
"""

import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

class Blockchain:
    def __init__(self):
        self.chain= []
        self.transactions=[]
        self.create_block(proof = 1, prev_hash='0')
        self.nodes= set()
        self.market_supply = 0
        
    def create_block(self, proof, prev_hash):
        block= {'index': len(self.chain)+1,
               'timestamp': str(datetime.datetime.now()),
               'proof': proof,
               'prev_hash': prev_hash,
               'transactions': self.transactions}
        self.transactions = []
        self.chain.append(block)
        return block
    def proof_of_work(self, prev_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - prev_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof
    def get_prev_block(self):
        return self.chain[-1]
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    def is_chain_valid(self,chain):
        prev_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['prev_hash'] != self.hash(prev_block):
                return False
            prev_proof = prev_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - prev_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            prev_block = block
            block_index += 1
        return True
    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({'sender' : sender,
                                  'receiver' : receiver,
                                  'amount' : amount})
        return self.get_prev_block()['index'] + 1
    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False
    
app = Flask( __name__)
#node_address = str(uuid4()).replace('-','')
blockchain = Blockchain()

class Wallet:
    def __init__(self):
        self.wallet_address = str(uuid4()).replace('-','')
        self.balance = 0
    def add_reward(self, reward):
        self.balance += reward
        
wallet = Wallet()
node_address = wallet.wallet_address

@app.route('/wallet_details', methods = ['GET'])
def wallet_details():
    response = {'wallet_address': node_address,
                'balance': wallet.balance}
    return jsonify(response), 200

@app.route('/mine_block', methods = ['GET'])
def mine_block():
    prev_block = blockchain.get_prev_block()
    prev_proof = prev_block['proof']
    proof = blockchain.proof_of_work(prev_proof)
    prev_hash = blockchain.hash(prev_block)
    blockchain.add_transaction(sender = 'Miner Reward', receiver = node_address, amount = 10)
    wallet.add_reward(10)
    blockchain.market_supply = blockchain.market_supply + 10
    block = blockchain.create_block(proof, prev_hash)
    response = {'message' : 'You just mined a block!',
                'index' : block['index'],
                'timestamp' : block['timestamp'],
                'proof' : block['proof'],
                'prev_hash' : block['prev_hash'],
                'transactions' : block['transactions']}
    return jsonify(response), 200
    
@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {'chain' : blockchain.chain,
                'length' : len(blockchain.chain)}
    return jsonify(response), 200

@app.route('/is_valid', methods=['GET'])
def is_valid():
    return jsonify(blockchain.is_chain_valid(blockchain.chain)), 200

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all (key in json for key in transaction_keys):
        return 'Recheck it out!', 400
    if json['sender'] != node_address:
        return 'Recheck sender address', 400
    #if json['receiver'] not in blockchain.balance.keys():
    #    return 'Receiver address does not exist', 400
    if wallet.balance < json['amount']:
        return 'Insufficient balance', 400
    index = blockchain.add_transaction(json['sender'], json['receiver'], json['amount'])
    response = {'message' : f'This transaction will be added to Block {index}'}
    return jsonify(response), 201

@app.route('/connect_node', methods=['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return 'Recheck it out!',400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message' : 'All the nodes are now connected. The safecoin Blockchain now contains the following nodes:',
                'total_nodes' : list(blockchain.nodes)}
    return jsonify(response), 201

@app.route('/refresh', methods=['GET'])
def refresh():
    cur_index = blockchain.get_prev_block()['index']
    is_chain_replaced= blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message' : 'Chain replaced by the longest one!',
                    'new_chain' : blockchain.chain}
        while cur_index + 1 != len(blockchain.chain):
            cur_index += 1
            for txn in blockchain.chain[cur_index]['transactions']:
                if txn['sender'] == node_address:
                    wallet.add_reward(-txn['amount'])

                elif txn['receiver'] == node_address:
                    wallet.add_reward(txn['amount'])
    else:
        response = {'message' : 'All good. The chain is the longest one!',
                    'chain' : blockchain.chain}
    return jsonify(response), 200
    
app.run(host = '0.0.0.0', port = 5001)
        

        
