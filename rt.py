#!usr/bin/env python
# -*- coding:utf-8 -*-



###	フォロー一覧の更新
def updateFollows(strLocFollows, arrayLog):

	#	jsonファイルとして保存されているフォロー一覧と各フォローのTweet取得状況を更新する。
	#	[
	#		'IDs': list
	#		'follow ID0': ['latest read tweet ID', 'count']
	#		'follow ID1': ['latest read tweet ID', 'count']
	#		...
	#	]
	#	ログを返す

	print ('Start - update follows')
	strLog = "Start - update follows \n"

	#	jsonを外部から読み込む
	f = open(strLocFollows)
	data = json.load(f)
	f.close

	#	最終的にファイルとして保存する辞書を初期化する
	dictFollows = {}

	#	APIを呼ぶにあたって例外処理
	try:
		#	フォロー一覧をAPIから取得する
		dictFollows['IDs'] = api.friends_ids()

		#	既存のフォローについてファイルから情報を読み込み、新規のフォローは情報を初期化
		for id in dictFollows['IDs']:
			if str(id) in data:
				dictFollows[str(id)] = data[str(id)]
			else:
				dictFollows[str(id)] = [0, 0]
		strLog += "Previous follows: " + str(len(data['IDs'])) + "\n"
		strLog += "Current follows: " + str(len(dictFollows['IDs'])) + "\n"

		#	アップデート後のフォロー一覧およびTweet取得状況を出力する
		f = open(strLocFollows, 'w')
		json.dump(dictFollows, f, indent = 4)
		f.close()
		print ('Done - Follows have been updated.')
		strLog += "Done - Follows have been updated.\n"

	#	例外処理
	except TweepError as e:
		print (e)
		strLog += str(e) + "\n"
		print ('Done - Follows have NOT been updated.')
		strLog += "Done - Follows have NOT been updated.\n\n"

	#	ログを返す
	arrayLog[0] += strLog

###	完了 --> フォロー一覧の更新



###	フォロー一覧から既探索回数の少ないユーザーを選んで過去Tweetを最大数まで取得する
def getFollowsTL(strLocFollows, intGetFollowLimit, intGetFollowTLLimit, arrayLog):

	print ('\nStart - dig follows past tweets')
	strLog = "\nStart - dig follows past tweets\n"

	#	フォロー一覧を読込
	f = open(strLocFollows)
	dictFollows = json.load(f)
	f.close

	#	TLを保持する配列を初期化
	arrayTimelines = []

	#	既探索回数の少ないユーザーから候補を探す
	#	最大2人までのユーザーのTweetを取得する
	intNumberuser = 0
	for count in range(99999):
		#	終了条件の判定
		if intNumberuser >= intGetFollowLimit:
			break
		for id in dictFollows['IDs']:
			#	終了条件の判定
			if intNumberuser >= intGetFollowLimit:
				break

			#	探索回数がヒットした場合ユーザーのTweetの取得に入る
			if int(dictFollows[str(id)][1]) == count:
				#	ブロックされていた場合、鍵がかかっていた場合の例外処理
				try:
					strLog += "Found user " + str(id) + " " + str(api.get_user(id).screen_name) + " with count " + str(count) + "\n"

					#	ユーザーの探索回数の更新および終了条件の更新
					dictFollows[str(id)][1] = count + 1
					intNumberuser += 1

					intMaxID = 999999999999999999
					intMinID = max(10, int(dictFollows[str(id)][0]))
					for i in range(intGetFollowTLLimit):
						#	intMaxIDより過去のTweetを3200件取得する
						#	Loopの最中であれば既読のTweetより古い最新の200Tweetを取得する
						#	過去の取得時に既読となったTweetまでさかのぼった場合は中断する
						arrayTimelines.extend(api.user_timeline(id=id, count=200, max_id=intMaxID-1, since_id=intMinID-1, include_rts=0))

						#	読み込んだTLが空だった場合終了
						if len(arrayTimelines) == 0:
							strLog += "0 new Tweet in user TL !!!!???? \n"
							break

						#	ユーザーの既読の状況を更新する
						if i == 0:
							dictFollows[str(id)][0] = arrayTimelines[0].id
						#	TLの既読の状況を更新する（開始点）
							intLatestID = arrayTimelines[0].id
							strLog += "Updated latest read ID to " + str(intLatestID) + "\n"

						#	次のループでTLの既読部分を取得しないように取得するMAXIDを変更する。
						intMaxID=arrayTimelines[len(arrayTimelines)-1].id
						strLog += "Loop " + str(i) + ", Loaded TL for " + str(len(arrayTimelines)) + " Tweets with MaxID " + str(intMaxID) + "\n"

						#	現在読み込んでいるTweetの最古のIDと過去の既読Tweetの最新のものを比較
						#	未読が存在しない場合ループを抜ける
						if intMinID >= intMaxID:
							strLog += "No more new Tweets in user TL\n"
							break

				#	例外発生時は当該IDの探索回数を最大値に設定して時間以降探索しないようにする
				#	今回のユーザーから抜け、次のユーザーの探索に処理を継続する
				except TweepError as e:
					dictFollows[str(id)][1] = 99999
					print (e)
					strLog += str(e) + "\n"
					break

				strLog += "Now loaded " + str(len(arrayTimelines)) + " Tweets" + "\n"
			

	#	アップデート後のフォロー一覧およびTweet取得状況を出力する
	f = open(strLocFollows, 'w')
	json.dump(dictFollows, f, indent = 4)
	f.close()

	print ("Done - dig follows past tweets")
	strLog += "Done - dig follows past tweets\n\n"

	#	Return
	arrayLog[0] += strLog
	return arrayTimelines

###	完了 --> フォローからユーザーを選択してTweetを取得する



###	自分の home timeline から最大1000件まで未読Tweetを取得する
def getHomeTL(strLocrecordTL, arrayLog):

	print ("Start - get home timelines")
	strLog = "\nStart - get home timelines\n"

	#	TLの既読の状況を取得
	f = open(strLocrecordTL)
	recordTL = json.load(f)
	f.close()

	strLog += "Initial Read Record:\n"

	for k,v in recordTL.items():
		print (k, v)
		strLog += str(k) + " " + str(v) + "\n"


	#	TLの未読最新Tweetを最大1000件取得する
	#	取得する最大のIDと最小のIDを指定、ここでは最大のIDはありえない大きな値を指定
	intMaxID = 999999999999999999
	intMinID = int(recordTL["latest_read"])

	#	TLを格納する配列を初期化する
	arrayTimelines = []

	#	intMaxIDより過去のTweetを最大1000件まで取得する
	#	Loopの最中であれば既読のTweetより古い最新の200Tweetを取得する
	try:
		for i in range(5):
			strLog += "Loop #" + str(i) + "; max_id = " + str(intMaxID) + "; since_id = " + str(intMinID) + "\n"

			#	TLの読込
			arrayTimelines.extend(api.home_timeline(count=200, max_id=intMaxID-1, since_id=intMinID-1, include_rts=0))
			strLog += "Loaded total " + str(len(arrayTimelines)) + " Tweets\n"

			#	読み込んだTLが空だった場合終了
			if len(arrayTimelines) == 0:
				strLog += "0 new Tweet in home TL !!!!???? \n"
				break

			#	次のループで読込を開始するTweet IDをアップデート
			intMaxID=arrayTimelines[len(arrayTimelines)-1].id

			#	次回起動時のために今回のTL読込の開始点を保存
			if i == 0:
				recordTL["latest_read"] = arrayTimelines[0].id
				strLog += "Updated latest read ID to " + str(recordTL["latest_read"]) + "\n"

			#	現在読み込んでいるTweetの最古のIDと過去の既読Tweetの最新のものを比較
			#	未読が存在しない場合ループを抜ける
			if intMinID >= intMaxID:
				strLog += "No more new Tweets in home TL\n"
				break

	except TweepError as e:
		print (e)
		strLog += str(e) + "\n"

	#	TLの既読の状況を更新しjsonに保存
	recordTL["oldest_read"] = intMinID

	strLog += "New Read Record:\n"
	for k,v in recordTL.items():
		print (k, v)
		strLog += str(k) + " " + str(v) + "\n"

	f = open(strLocrecordTL, 'w')
	json.dump(recordTL, f, indent=4)
	f.close()

	print ("Done - get home timelines")
	strLog += "Done - get home timelines\n\n"

	#	Return
	arrayLog[0] += strLog
	return arrayTimelines

###	完了 --> 自分のhome timelineを取得する


#	TLの辞書の配列から画像付きTweetでかつ過去にRTされたことのないものを抽出して以下の辞書を返す
def extractPicTweet(arrayTimelines, arrayLog):

	#	[
	#		'listIDs': list
	#		'tweetID0': [RT count, fav count, creation time]
	#		'tweetID1': [RT count, fav count, creation time]
	#		...
	#	]

	#	抽出したTweetのIDと情報を格納する配列と辞書の初期化
	dictIDs = {}
	dictIDs["listIDs"] = []
	strLog = ""

	#	画像付きTweetでかつRT済でないものを抽出
	print ("Start - extract Pic Tweets")
	strLog += "Start - extract Pic Tweets\n"

	print ("Input = " + str(len(arrayTimelines)) + " tweets") 
	strLog += "Input = " + str(len(arrayTimelines)) + " tweets\n" 

	for item in arrayTimelines:
		if 'media' in item.entities:
			if item.entities['media'][0].get('type') == "photo":
				if not item.retweeted:
					dictIDs["listIDs"].append(item.id)
					dictIDs[str(item.id)] = [item.retweet_count, item.favorite_count, item.created_at.timestamp()]

	print ("Done - Extracted = " + str(len(dictIDs["listIDs"])) + " tweets")
	strLog += "Done - Extracted = " + str(len(dictIDs["listIDs"])) + " tweets\n\n"

	#	Return
	arrayLog[0] += strLog
	return dictIDs

###	完了 --> TLの辞書の配列から画像付きTweetでかつ過去にRTされたことのないものを抽出して以下の辞書を返す


#	TweetをRTするか否かを判定
#	入力：TweetのIDと情報の辞書、最大get_statusAPI回数、Passの辞書、Rejectの辞書
#	出力：PassしたTweetのIDと情報の辞書、RejectしたTweetのIDと情報の辞書、使用したget_statusAPI回数
#	渡されたPass/Rejectそれぞれの辞書を直接操作する
def reviewTweets(dictIDs, intAPI, dictPassIDs, dictRejectIDs, arrayLog):

	print ("Start - review tweets " + str(len(dictIDs["listIDs"])) + " tweets, " + "Get API = " + str(intAPI))
	strLog = "Start - review tweets " + str(len(dictIDs["listIDs"])) + " tweets, " + "Get API = " + str(intAPI) + "\n"

	intRTThreshold = int(inifile.get("parameter", "RTthreshold"))
	intFavThreshold = int(inifile.get("parameter", "favthreshold"))
	intShuffleStart = int(inifile.get("parameter", "shufflebegin"))
	insShuffleEnd = int(inifile.get("parameter", "shuffleend"))
	intAdjThreshold = int(inifile.get("parameter", "adjthreshold"))
	intTTLThreshold = int(inifile.get("parameter", "TTLthreshold"))
	intAdjustmentFactor = 1
	floatNow = datetime.now().timestamp() - 9 * 60 * 60
	intConsumedAPI = 0
	intRemovalCounter = 0
	intInitialPass = len(dictPassIDs["listIDs"])
	intInitialReject = len(dictRejectIDs["listIDs"])

	#	現在時刻が深夜2時から午前8時までの間であればlistIDsをシャッフルする
	#	投稿順の降順にソートされている状態で氷菓を開始すると常に新しいのTweetが優先して情報の更新を受ける。
	#	古いTweetに再評価の機会を与えるための処理である
	if datetime.now().hour >= intShuffleStart and datetime.now().hour < insShuffleEnd:
		random.shuffle(dictIDs["listIDs"])
		strLog += str(datetime.now().hour) + " o'clock -> tweets shuffled\n"

	a = []

	for id in dictIDs["listIDs"]:
		a = dictIDs[str(id)]

		#	閾値の調整係数を設定
		#	投稿時間が1時間以内か否かの判定
		if floatNow - a[2] <= intAdjThreshold:
			intAdjustmentFactor = 2
		else: 
			intAdjustmentFactor = 1

		#	RT閾値の判定
		if a[0] > intRTThreshold / intAdjustmentFactor and a[1] > intFavThreshold / intAdjustmentFactor:
			dictPassIDs["listIDs"].append(id)
			dictPassIDs[str(id)] = a
		#	情報の更新無しでは閾値を超えなかった場合
		else:
			#	情報の更新の有無を判定
			#	残APIがある場合は更新し再判定、更新後の判定では1日以上経過したものは削除
			#	残APIがない場合は原則Reject、ただし、APi設定が-1の場合更新前であっても1日以上経過したものは削除
			if intAPI > intConsumedAPI:
				try:
					intConsumedAPI += 1
					dictTemp = api.get_status(id)
					a[0] = dictTemp.retweet_count
					a[1] = dictTemp.favorite_count
					#	RT閾値の判定
					if a[0] > intRTThreshold / intAdjustmentFactor and a[1] > intFavThreshold / intAdjustmentFactor:
						dictPassIDs["listIDs"].append(id)
						dictPassIDs[str(id)] = a
					elif floatNow - a[2] <= intTTLThreshold:
						dictRejectIDs["listIDs"].append(id)
						dictRejectIDs[str(id)] = a
					else:
						intRemovalCounter += 1
				except TweepError as e:
					print (e)
					strLog += str(e) + "\n"
					strLog += "Removed " + str(id) + "\n"
					intRemovalCounter += 1
			else:
				if intAPI == -1 and floatNow - a[2] > intTTLThreshold:
					intRemovalCounter += 1
				else:
					dictRejectIDs["listIDs"].append(id)
					dictRejectIDs[str(id)] = a

	print ("Done - Pass = " + str(len(dictPassIDs["listIDs"]) - intInitialPass) + " tweets; Reject = " + str(len(dictRejectIDs["listIDs"]) - intInitialReject) + " tweets")
	print ("       Removed = " + str(intRemovalCounter) + " tweets; Consumed API: " + str(intConsumedAPI))
	strLog += "Done - Pass = " + str(len(dictPassIDs["listIDs"]) - intInitialPass) + " tweets; Reject = " + str(len(dictRejectIDs["listIDs"]) - intInitialReject) + " tweets\n"
	strLog += "       Removed = " + str(intRemovalCounter) + " tweets; Consumed API: " + str(intConsumedAPI) + "\n"
	arrayLog[0] += strLog	

	return intConsumedAPI

###	完了 --> TweetをRTするか否かを判定


#####	ここからmain関数 	#####
if __name__ == "__main__":

	### 初期設定
	#	ライブラリ読込: tweepy, json, datetime, time, random
	#	設定ファイル読込と変数へのセット
	#	TwitterのauthログインとAPIインスタンスの作成

	##	ライブラリ読込
	import tweepy
	from tweepy import *
	import json
	import datetime
	from datetime import *
	import time
	import random
	import configparser

	##	設定ファイルの読込
	inifile = configparser.SafeConfigParser()
	inifile.read("./config.ini")
	#	I/Oファイルの場所
	authfile = inifile.get("auth", "authfile")
	strLocFollows = inifile.get("file", "follows")
	strLocrecordTL = inifile.get("file", "recordTL")
	strLocpicTweets = inifile.get("file", "picTweets")
	strLoctargetTweets = inifile.get("file", "targetTweets")
	strLocrtedTweets = inifile.get("file", "rtedTweets")
	strLoclog = inifile.get("file", "log")
	#	パラメータの設定（APIリミット関連）
	intGetFollowLimit = int(inifile.get("parameter", "getfollow"))
	intGetFollowTLLimit = int(inifile.get("parameter", "getfollowTL"))
	intGetHomeTLLimit = int(inifile.get("parameter", "gethomeTL"))
	intGetAPILimit = int(inifile.get("parameter", "getAPIlimit"))
	intRTLimit = int(inifile.get("parameter", "RTAPIlimit"))
	intRTminLimit = int(inifile.get("parameter", "RTminAPIlimit"))

	##	TwitterへのAuthログインとAPIインスタンスの作成
	f = open(authfile)
	authDict = json.load(f)
	f.close()
	CONSUMER_KEY = authDict["CONSUMER_KEY"]
	CONSUMER_SECRET = authDict["CONSUMER_SECRET"]
	auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
	ACCESS_TOKEN = authDict["ACCESS_TOKEN"]
	ACCESS_SECRET = authDict["ACCESS_SECRET"]
	auth.set_access_token (ACCESS_TOKEN, ACCESS_SECRET)
	#	APIインスタンスを作成
	api = tweepy.API(auth)

	##	完了メッセージ
	print ('Done - initilization')
	arrayLog = ["Done - initilization\n"]

	###	完了 --> 初期設定


	#	ログ用の変数作成
	arrayLog[0] += "\n\n\n*****\n\nLaunched at " + str(datetime.now()) + "\n"

	#	自分の情報を取得
	myID = api.me().id
	print(str(myID) + " shall be used for this session")
	arrayLog[0] += str(myID) + " shall be used for this session\n\n"

	#	フォロー一覧の情報の更新
	updateFollows(strLocFollows, arrayLog)

	#	RT判定後のTweetのIDと情報を格納する辞書を初期化
	dictPassIDs = {}
	dictPassIDs["listIDs"] = []
	dictRejectIDs = {}
	dictRejectIDs["listIDs"] = []

	#	RT対象TweetのIDの辞書の読込/RT判定
	print ("Start - review RT target tweets")
	arrayLog[0] += "\nStart - review RT target tweets\n"
	f = open(strLoctargetTweets)
	dictoldIDsTarget = json.load(f)
	f.close()
	intGetAPILimit -= reviewTweets(dictoldIDsTarget, intGetAPILimit, dictPassIDs, dictRejectIDs, arrayLog)
 
	#	画像付きTweetのIDの辞書を読み込む
	print ("Start - review pic tweets")
	arrayLog[0] += "\nStart - review pic tweets \n"
	f = open(strLocpicTweets)
	dictoldIDsPict = json.load(f)
	f.close()
	intGetAPILimit -= reviewTweets(dictoldIDsPict, intGetAPILimit, dictPassIDs, dictRejectIDs, arrayLog)

	#	user timeline の読込/画像付きTweetを抽出/RT判定
	arrayTimelines = getFollowsTL(strLocFollows, intGetFollowLimit, intGetFollowTLLimit, arrayLog)
	dictUserExtract = extractPicTweet(arrayTimelines, arrayLog)
	intGetAPILimit -= reviewTweets(dictUserExtract, -1, dictPassIDs, dictRejectIDs, arrayLog)

	#	home timeline の読込/画像付きTweetを抽出/RT判定
	arrayTimelines = getHomeTL(strLocrecordTL, arrayLog)
	dictHomeExtract = extractPicTweet(arrayTimelines, arrayLog)
	intGetAPILimit -= reviewTweets(dictHomeExtract, -1, dictPassIDs, dictRejectIDs, arrayLog)

	#	RT候補Tweet/画像付TweetのIDを含む配列(dictPassIDs["listIDs"]およびdictRejectIDs["listIDs"])を降順ソート
	print ("Before sort: " + str(len(dictPassIDs["listIDs"])) + " tweets")
	dictPassIDs["listIDs"] = list(set(dictPassIDs["listIDs"]))
	dictPassIDs["listIDs"].sort(reverse = True)
	print ("After sort: " + str(len(dictPassIDs["listIDs"])) + " tweets, dict = " + str(len(dictPassIDs)) + " keys")
	print ("Before sort: " + str(len(dictRejectIDs["listIDs"])) + " tweets")
	dictRejectIDs["listIDs"] = list(set(dictRejectIDs["listIDs"]))
	dictRejectIDs["listIDs"].sort(reverse = True)
	print ("After sort: " + str(len(dictRejectIDs["listIDs"])) + " tweets, dict = " + str(len(dictRejectIDs)) + " keys")


	#	RT済TweetのIDと情報を格納する辞書を読み込む
	f = open(strLocrtedTweets)
	dictIDsrted = json.load(f)
	f.close()

	#	RTの実施
	#	1時間以内に投稿されたTweetであれば指定されたAPI呼び出し回数の限界までRT
	#	1時間以内に投稿されたTweetが最低RT回数に満たない場合はシャッフルして古いTweetを最低RT回数までRT
	print ("Start - RT process")
	arrayLog[0] += "\nStart - RT process \n"

	floatNow = datetime.now().timestamp() - 9 * 60 * 60
	intRTCounter = 0

	for i in range(intRTLimit):
		try:
			intTempID = dictPassIDs["listIDs"][0]
			#	対象Tweetが投稿されてから1時間以上経過しているか判定
			if floatNow - dictPassIDs[str(intTempID)][2] > 3600:
				#	RT回数が最低回数を超えているか判定
				#	超過：ループから抜ける / 非超過：Tweetの配列をシャッフルして保持しているIDを更新
				if intRTCounter >= intRTminLimit:
					break
				else:
					random.shuffle(dictPassIDs["listIDs"])
					intTempID = dictPassIDs["listIDs"][0]
					print ("Next tweet is over 1hr life")
					arrayLog[0] += "Next tweet is over 1hr life\n"
			#	RTの実施とRTしたIDおよび情報の転送、削除
			api.retweet(intTempID)
			print ("RT: " + str(intTempID) + ", RT = " + str(dictPassIDs[str(intTempID)][0]) + ", fav = " + str(dictPassIDs[str(intTempID)][1]) + ", created at " + str(datetime.fromtimestamp(dictPassIDs[str(intTempID)][2]).isoformat()))
			arrayLog[0] += "RT: " + str(intTempID) + ", RT = " + str(dictPassIDs[str(intTempID)][0]) + ", fav = " + str(dictPassIDs[str(intTempID)][1]) + ", created at " + str(datetime.fromtimestamp(dictPassIDs[str(intTempID)][2]).isoformat()) + "\n"
			dictIDsrted["listIDs"].append(intTempID)
			dictIDsrted[str(intTempID)] = dictPassIDs[str(intTempID)]
			dictPassIDs["listIDs"].remove(intTempID)
			del dictPassIDs[str(intTempID)]
			intRTCounter += 1

		except TweepError as e:
			dictPassIDs["listIDs"].remove(intTempID)
			del dictPassIDs[str(intTempID)]
			intRTCounter += 1		
			print (e)
			arrayLog[0] += str(e) + "\n"
			arrayLog[0] += "Removed " + str(intTempID) + "\n"

	print ("End - RT process")
	arrayLog[0] += "End - RT process \n"


	#	新しく作りなおしたTweetのIDと情報の辞書を保存する
	print ("\nStart - save tweets dict")
	dictPassIDs["listIDs"].sort(reverse = True)
	arrayLog[0] += "Start - save tweets dict\n"
	f = open(strLoctargetTweets, 'w')
	json.dump(dictPassIDs, f, indent = 4)
	f.close()
	f = open(strLocpicTweets, 'w')
	json.dump(dictRejectIDs, f, indent = 4)
	f.close()
	f = open(strLocrtedTweets, 'w')
	json.dump(dictIDsrted, f, indent = 4)
	f.close()
	print ("Done - save tweets dict")
	arrayLog[0] += "Done - save tweets dict\n"

	#	APILimitを取得する
	try:
		dictAPILimit = api.rate_limit_status()
		arrayLog[0] += "\nAPI Limit:\n"
		arrayLog[0] += "Credential " + str(dictAPILimit['resources']['account']['/account/verify_credentials']['remaining']) + "\n"
		arrayLog[0] += "TL " + str(dictAPILimit['resources']['statuses']['/statuses/home_timeline']['remaining']) + "\n"
		arrayLog[0] += "User TL " + str(dictAPILimit['resources']['statuses']['/statuses/user_timeline']['remaining']) + "\n"
		arrayLog[0] += "Get Tweet " + str(dictAPILimit['resources']['statuses']['/statuses/show/:id']['remaining']) + "\n"
		arrayLog[0] += "API Limit " + str(dictAPILimit['resources']['application']['/application/rate_limit_status']['remaining']) + "\n"
		arrayLog[0] += "Next Reset " + str(time.localtime(int(dictAPILimit['resources']['statuses']['/statuses/show/:id']['reset']))) + "\n"
	except TweepError as e:
		print (e)
		arrayLog[0] += str(e) + "\n"
		arrayLog[0] += "Failed to load API limit\n"

	arrayLog[0] += "\nFinished at " + str(datetime.now()) +"\n\n\n" 

	#	ログファイルの書き込み
	f=open(strLoclog, 'a')
	f.write(arrayLog[0])
	f.close()


