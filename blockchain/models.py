from random import randrange

from django.db import models
from django.contrib.postgres.fields import JSONField
import hashlib
from django.utils import timezone
import json

def hash(timestamp, data, previous):
	sha = hashlib.sha256()
	line = str(timestamp) + str(data) + str(previous)
	sha.update(line.encode('utf-8'))
	return sha.hexdigest()


# Create your models here.
class BlockManager(models.Manager):

	def get_queryset(self):
		return BlockQuerySet(self.model, using=self.db)


class BlockQuerySet(models.QuerySet):

	def list_dict(self):
		serialized_data = []
		for block in self:
			serialized_data.append(block.serialize())
		return serialized_data

	def get_by_hash(self, hash):
		for block in self:
			if hash == block.hash_block():
				return block
		return None


class Block(models.Model):

	objects = BlockManager()

	def serialize(self):
		result = {
			'id':self.pk,
			'timestamp':str(self.timestamp),
			'data': self.data,
			'proof_of_work': self.proof_of_work,
			'previous':self.previous,
			'hash': self.hash_block()
		}
		return result

	@classmethod
	def create(cls, data, previous_hash, proof_of_work):
		block = cls(data=data,
				   previous=previous_hash,
				   proof_of_work=proof_of_work,
				   timestamp=timezone.now())
		block.hash_block()
		return block


	@staticmethod
	def get_genesis_block():
		chain = Block.objects.all()
		for block in chain:
			if block.previous == "0":
				return block

		return None

	def is_genesis_block(self):
		if self.previous == "0":
			return True
		else:
			return False

	@staticmethod
	def get_last_block():
		block = Block.objects.order_by('-timestamp').first()
		block.hash = block.hash_block()
		return block

	def hash_block(self):
		return hash(self.timestamp, self.data, self.previous)

	def __str__(self):
		index = "Not set yet" if self.id is None else self.id
		return f"id: {index}\ntime: {self.timestamp}\ndata: {self.data}" \
			f"\nprevious: {self.previous}\nPOW: {self.proof_of_work}\nhash: {self.hash_block()}"

	timestamp = models.DateTimeField()
	data = JSONField(null=False, blank=False)
	proof_of_work = models.TextField(null=False, blank=False)
	previous = models.TextField(null=False, blank=False)
