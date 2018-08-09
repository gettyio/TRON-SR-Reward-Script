import json
import urllib2
import requests
import base58
import time
from datetime import datetime
import logging

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.basicConfig(level=logging.DEBUG, filename='sr.log')

SELF_ADDRESS = ""
PK = ""
DIST_PERCENT = 90.0

def hexTRONAddress(address):
  return base58.b58decode_check(address.encode()).encode("hex")


def base58TRONAddress(address):
  return base58.b58encode_check(str(bytearray.fromhex( address )))

def broadcastTxnJSON(data):
  # SIGN DATA

  data_dict = json.loads(data)

  sign_dict = {'transaction':data_dict, 'privateKey':PK}

  post_data = json.dumps(sign_dict, separators=(',',':'))
  url = "http://127.0.0.1:8090/wallet/gettransactionsign"

  r = requests.post(url, data=post_data, allow_redirects=True)


  # BROADCASTS DATA

  broadcast_url = "http://127.0.0.1:8090/wallet/broadcasttransaction"

  r2 = requests.post(broadcast_url, data=r.content, allow_redirects=True)

def generateTransferTxn(sendAddress, amount):

  post_dict = {'owner_address':hexTRONAddress(SELF_ADDRESS), 'to_address':hexTRONAddress(sendAddress), 'amount':amount}

  post_data = json.dumps(post_dict, separators=(',',':'))
  url = "http://127.0.0.1:8090/wallet/createtransaction"

  r = requests.post(url, data=post_data, allow_redirects=True)
  return r.content

def getAccountSRAwards():
  sign_dict = {'address':hexTRONAddress(SELF_ADDRESS)}

  post_data = json.dumps(sign_dict, separators=(',',':'))
  url = "http://127.0.0.1:8090/wallet/getaccount"

  r = requests.post(url, data=post_data, allow_redirects=True)
  content = json.loads(r.content)
  return content["allowance"]


def withdrawSRAwards():
  sign_dict = {'owner_address':hexTRONAddress(SELF_ADDRESS)}

  post_data = json.dumps(sign_dict, separators=(',',':'))
  url = "http://127.0.0.1:8090/wallet/withdrawbalance"

  r = requests.post(url, data=post_data, allow_redirects=True)
  return "ContractValidateException" not in r.content:


def getNowBlockID():
  url = "http://127.0.0.1:8090/wallet/getnowblock"

  r = requests.post(url, allow_redirects=True)

  # Get current block
  current_block_data = r.content

  current_block = json.loads(current_block_data)
  current_block_id = current_block["block_header"]["raw_data"]["number"]
  return current_block_id


def getVotersFromStart(start, address, sr_rewards):
  time.sleep(.1)
  response = urllib2.urlopen("https://api.tronscan.org/api/vote?limit=100&start="+str(start)+"&sort=timestamp&candidate="+address).read()
  voter_data = json.loads(response)

  # Iterate data, pull all voter list
  voters = voter_data['data']
  total_votes = voter_data['totalVotes']

  votersList = [];

  for voter in votersList:
    percentage = (float(voter['votes']) / float(total_votes))

    voter_data = {}
    voter_data["address"] = voter['voterAddress']
    voter_data["votes"] = voter['votes']
    voter_data["percentage"] = percentage
    voter_data["award_amount"] = int(percentage * sr_rewards)
    votersList.append(voter_data)

  return votersList


def getVoteDataForAddress(address):
  response = urllib2.urlopen("https://api.tronscan.org/api/vote?limit=100&start=0&sort=timestamp&candidate="+address).read()

  voter_data = json.loads(response)
  total_votes = voter_data['totalVotes']

  total_voters = voter_data['total']

  # Paginate the requests so that you can handle this properly
  currentPage = 0
  totalVotersList = []

  sr_rewards = float(getAccountSRAwards() * DIST_PERCENT / 100.0)

  while (total_voters - currentPage > 0):
    totalVotersList = totalVotersList + getVotersFromStart(currentPage,address,sr_rewards)
    currentPage += 100

  output = {}

  output["voters"] = len(totalVotersList)
  output["totalVotes"] = total_votes

  output["payTable"] = totalVotersList
  output["currentBlock"] = getNowBlockID()
  output["availableAllowance"] = float(getAccountSRAwards() * DIST_PERCENT / 100.0)

  output["logTime"] = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

  return output


def processSRREwardsDistribution():
  # Calculate vote data
  votersList = getVoteDataForAddress(SELF_ADDRESS)

  # print "Starting"
  logging.debug('SR REWARD Log:%s: %s\n\n',str(datetime.now().strftime('%Y-%m-%d')), votersList)

  # Claim Rewards
  claim_success = withdrawSRAwards()

  if not claim_success:
    logging.debug('SR REWARD CLAIM FAILED')
    exit()

  # print "Continuing"
  logging.debug('SR REWARD Claimed')

  # Distribute Rewards
  for voter in votersList["payTable"]:

    if voter["address"] != SELF_ADDRESS:
      broadcastTxnJSON(generateTransferTxn(voter["address"], voter["award_amount"]))
      time.sleep(.1)

  # print "Distributed"
  logging.debug('SR REWARD DISTRIBUTED')


processSRREwardsDistribution()





