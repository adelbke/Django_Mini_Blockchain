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
	return HttpResponse(json.dumps(BlockChain.check_chain(chain)))

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
					raise Exception('Blockchain is faulty')
				else:
					if current.proof_of_work % 9 == 0 and current.proof_of_work % previous_block.proof_of_work == 0:
						# if the proof of work is correct we move on
						current = Block.objects.all().get_by_hash(current.previous)
					else:
						# otherwise we throw a an error
						raise Exception('Faulty Blockchain')


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
		i = 0
		current = last_block
		while i < len(chain):
			if current.get('hash') != hash(current['fields']['timestamp'],
									   current['fields']['data'],
									   current['previous']):
	# 			faulty chain
				return False
			else:
				current = BlockChain.__get_block_with_hash(current['previous'], chain)
				i += 1
		return True

	@staticmethod
	def __get_last_block(external_chain):
		biggest = external_chain[0]
		for block in external_chain:
			if block['fields']['timestamp'] > biggest['fields']['timestamp']:
				biggest = block

		return biggest

	@staticmethod
	def __get_block_with_hash(value,chain):
		for block in chain:
			if hash(block['fields']['timestamp'],block['fields']['data'],block['previous']) == value:
				return block
		return None

	@staticmethod
	def concensus(external_chain):
		# chain should be a list containing dictionaries
		chain = Block.objects.all().order_by('timestamp').values()

		# we first verify the length of each chain
		if chain.count() > len(external_chain):
			# our chain is longer

			for block in chain:
				pass

		pass
