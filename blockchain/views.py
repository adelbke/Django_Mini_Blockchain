from django.db.models import Count, F
from django.shortcuts import render
from .models import Block
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, HttpResponseForbidden
import json
import random
from .models import hash
# Create your views here.


def get_blocks(request):
	items = BlockChain.get_blocks()

	# data = serializers.serialize('json',items)
	data = json.dumps(items)
	return HttpResponse(data)

def mine_block(request):
	if request.method == 'GET':
		return HttpResponseForbidden
	block_data = json.loads(request.body.decode('utf-8'))
	block = BlockChain.add_block(block_data)
	data = json.dumps(block.serialize())
	return HttpResponse(data)

# this is when two nodes want to update their chains
# in here we receive a chain we verify it and apply concensus,send ours as a response
def concensus(request):
	if request.method == 'GET':
		return HttpResponseForbidden
	chain = json.loads(request.body.decode('utf-8'))

	original_chain = BlockChain.get_blocks()

	BlockChain.consensus(chain)

	return HttpResponse(json.dumps(original_chain))

class BlockChain:

	@staticmethod
	def init():
		# initialize the Blockchain
		# 	check if the blockchain is empty
		if Block.objects.all().count() == 0:
			# add the genesis block
			BlockChain.genesis_block()

	@staticmethod
	def genesis_block():
		data_dictionary = {
			'Content':'This is the Genesis Block data'
		}
		block = Block.create(data_dictionary, "0", random.randrange(5,200))
		block.save()
		return block

	@staticmethod
	def check():
		# we fetch the last block
		last = Block.get_last_block()
		condition = True
		current = last
		while condition:
			if current.is_genesis_block():
				condition = False
				return True
			else:
				previous_block = Block.objects.all().get_by_hash(current.previous)
				if current.previous != previous_block.hash_block():
					return False
				else:
					if current.proof_of_work % 9 == 0 and current.proof_of_work % previous_block.proof_of_work == 0:
						# if the proof of work is correct we move on
						current = Block.objects.all().get_by_hash(current.previous)
					else:
						# otherwise we throw a an error
						return False


	@staticmethod
	def __proof_of_work(previous_proof):
		previous_proof = int(previous_proof)
		i = previous_proof + 1

		while not (i % 9 == 0 and i % previous_proof == 0):
			i += 1
		return i

	@staticmethod
	def add_block(data):
		if BlockChain.check() is True:
			last_item = Block.get_last_block()

			if last_item is None:
				last_item = BlockChain.genesis_block()
			# calculate proof of work
			pow = BlockChain.__proof_of_work(last_item.proof_of_work)

			block = Block.create(data, last_item.hash_block(), pow)
			block.save()
			return block
		else:
			raise Exception('Blockchain is faulty')

	@staticmethod
	def get_blocks():
		BlockChain.init()
		data = Block.objects.all().list_dict()
		result = {
			'list':data,
			'count':Block.objects.all().count()
		}
		return data


	@staticmethod
	def check_chain(chain):
		last_block =  BlockChain.__get_last_block(chain)
		current = last_block
		condition = True
		i = 1
		while condition:
	# 		we verify if this block is the genesis block
	# 		this means two things, either the data has been compromised and the genesis block is the last block
	# 		Or it's an empty chain with one block
			if BlockChain.__check_if_genesis(current):
				if i == len(chain):
	# 				chain valid
					return True
				else:
					# invalid chain
					return False

	# 		we continue by acquiring the previous block, this block has been found with the exposed value
			try:
				previous_block = BlockChain.__get_block_with_hash(current['previous'],chain)
			except:
				return False
	# 		if the block is available we verify the proof of work
			if int(current['proof_of_work']) % 9 == 0 and int(current['proof_of_work']) % int(previous_block['proof_of_work']) == 0:
			# 	if the proof of work is valid we go forward in the Blockchain
				current = previous_block
				i += 1
			else:
				return False

	@staticmethod
	def __get_last_block(external_chain):
		biggest = external_chain[0]
		for block in external_chain:
			if block['timestamp'] > biggest['timestamp']:
				biggest = block

		return biggest

	@staticmethod
	def __check_if_genesis(external_block):
		data_dictionary = {
			'Content': 'This is the Genesis Block data'
		}
		if external_block['previous'] == "0" and external_block['data'] == data_dictionary:
			return True
		else:
			return False

	@staticmethod
	def __get_block_with_hash(value,chain):
		block_by_value = None
		block_by_hash = None
		for block in chain:
			# we save the block found by the value
			if block['hash'] == value:
				block_by_value = block
			# we save the block found by the hash
			if hash(block['timestamp'],block['data'],block['previous']) == value:
				block_by_hash = block
			# if we saved both, we exit the loop
			if block_by_value is not None and block_by_hash is not None:
				break;

		# we verify if there's integrity
		if block_by_value == block_by_hash:
			return block_by_value
		else:
			raise Exception('Blockhain faulty!')

	consensus_outcome = {
		0:'external chain Faulty and Rejected',
		1: 'internal chain faulty and accepted external Chain',
		2: 'external chain longer and accepted',
		3: 'internal chain longer'
	}
	@staticmethod
	def consensus(external_chain):
		# chain should be a list containing dictionaries
		chain = Block.objects.all().list_dict()

		# we return a code
		# 0 external chain Faulty and Rejected
		# 1 internal chain faulty and accepted external Chain
		# 2 external chain longer and accepted
		# 3 internal chain longer
		# we first check if any of the chains is faulty
		if not BlockChain.check():
		# 	our chain is faulty so we accept the external node's chain
		# 	we delete our chain
			Block.objects.all().delete()
		# 	we add the external items
			previous = "0"
			for block in external_chain:
				item = Block(timestamp=block['timestamp'],
							 data=block['data'],
							 proof_of_work=block['proof_of_work'],
							 previous=previous)
				item.save()
				previous = block['hash']
			return 1
		else:
			# if the external chain is invalid we don't take it into consideration
			if not BlockChain.check_chain(external_chain):
				return 0
			else:
# 				any of the chains is faulty,
# 				we take the longest one
				if len(chain) > len(external_chain):
# 					we change nothing the internal chain is the longest
					return 3
				else:
					# 	we delete our chain
					Block.objects.all().delete()
					# 	we add the external items
					previous = "0"
					for block in external_chain:
						item = Block(timestamp=block['timestamp'],
									 data=block['data'],
									 proof_of_work=block['proof_of_work'],
									 previous=previous)
						item.save()
						previous = block['hash']
					return 2
