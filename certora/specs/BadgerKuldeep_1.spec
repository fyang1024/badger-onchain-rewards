import "base.spec"

// epoch, reward, handle deposit, handle withdrawn, handle deposit and notify transfer related properties here 

// valid state
// verified
invariant non_initialized_epoch(uint256 epochId)
    epochId > currentEpoch() => getEpochsStartTimestamp(epochId) == 0 &&  getEpochsEndTimestamp(epochId) == 0

// valid state
// verified
invariant initialized_epoch(uint256 epochId)
    epochId > 0 && epochId <= currentEpoch() => getEpochsEndTimestamp(epochId) == getEpochsStartTimestamp(epochId) + SECONDS_PER_EPOCH()

// state transition
// verified
rule non_initialized_to_initialized_epoch(method f) {
    env e;
    calldataarg args;
    uint256 epochId;
    uint256 currentEpoch = currentEpoch();
    require epochId == currentEpoch + 1;

    uint256 epochIdStartTimeStampBeforeInitialization = getEpochsStartTimestamp(epochId);
    uint256 epochIdEndTimeStampBeforeInitialization = getEpochsEndTimestamp(epochId);

    require epochIdStartTimeStampBeforeInitialization == 0 && epochIdEndTimeStampBeforeInitialization == 0;
    f(e,args);

    uint256 epochIdStartTimeStampAfterInitialization = getEpochsStartTimestamp(epochId);
    uint256 epochIdEndTimeStampAfterInitialization = getEpochsEndTimestamp(epochId);

    assert epochIdStartTimeStampAfterInitialization != 0 && epochIdEndTimeStampAfterInitialization != 0 => f.selector == startNextEpoch().selector, "epoch started without invoking startNextEpoch";
}

// unit test
// verified
rule start_next_epoch_work_as_expected() {
    env e;

    uint epochDuration = SECONDS_PER_EPOCH();
    uint256 currentEpochId = currentEpoch();
    uint256 currentEpochEndTimestamp = getEpochsEndTimestamp(currentEpochId);

    uint256 currentTimestamp = e.block.timestamp;
    require currentTimestamp > currentEpochEndTimestamp;
    startNextEpoch(e);

    uint256 nextEpochId = currentEpoch();
    uint256 nextEpochStartTimestamp = getEpochsStartTimestamp(nextEpochId);
    uint256 nextEpochEndTimestamp = getEpochsEndTimestamp(nextEpochId);

    assert nextEpochId == currentEpochId + 1, "next epoch id should be 1 plus current one";
    assert nextEpochEndTimestamp == nextEpochStartTimestamp + epochDuration, "epoch end duration must be start duration plus 7 days in seconds";
    
}

// variable transition
// verified
rule current_epoch_non_decreasing(method f) filtered {f -> !f.isView} {
	uint256 currentEpoch = currentEpoch();
		
	env e;
    calldataarg args;
    f(e,args);
	uint256 updatedCurrentEpoch = currentEpoch();

    assert updatedCurrentEpoch == currentEpoch || ((updatedCurrentEpoch > currentEpoch) && (updatedCurrentEpoch == currentEpoch + 1)), "current epoch value must be non decreasing";
	
}

// variable transition
// verified
rule reward_token_only_added_by_addRewards_or_addReward(method f) {
    address rewardToken;
    uint256 tokenBalanceOfBefore = tokenBalanceOf(rewardToken, currentContract);

    env e;
    calldataarg args;

    f(e,args);
    uint256 tokenBalanceOfAfter = tokenBalanceOf(rewardToken, currentContract);

    assert tokenBalanceOfAfter > tokenBalanceOfBefore => 
        (f.selector ==  addReward(uint256 , address , address, uint256).selector)
        || (f.selector ==  addRewards(uint256[] , address[] , address[], uint256[]).selector), "reward token balance increase by some unknown method";
}

// unit test
// verified
rule add_reward_work_as_expected() {
    env e;
    uint256 epochId;
    address vault;
    address token;
    uint256 amount;

    uint256 currentEpochId = currentEpoch();
    uint256 tokenRewardsBefore = getRewards(epochId,vault,token);
    uint256 tokenBalanceOfBefore = tokenBalanceOf(token, currentContract);
    
    // need to add this require, considering token balance in RM contract will be greater than rewards amount
    require tokenBalanceOfBefore >= tokenRewardsBefore;
    require epochId >= currentEpochId;

    addReward(e, epochId, vault, token, amount);

    uint256 tokenRewardsAfter = getRewards(epochId,vault,token);
    uint256 tokenBalanceOfAfter = tokenBalanceOf(token, currentContract);

    assert tokenBalanceOfAfter >= tokenBalanceOfBefore, "token balance must be non decreasing";
    assert tokenRewardsAfter  >= tokenRewardsBefore, "total rewards must be non decreasing";
    assert tokenBalanceOfAfter >= tokenRewardsAfter, "token balance either greater than or equal to token reward amount";
}

// variable transtition
// verified
rule user_share_and_total_supply_non_decreasing_when_user_deposits() {
    env e;

    uint256 epochId = currentEpoch();
    address vault;
    
    address to;
    uint256 amount;

    uint256 userShareBeforeDeposit = getShares(epochId, vault, to);
    uint256 totalSupplyBeforeDeposit = getTotalSupply(epochId, vault);

    handleDeposit(e,vault,to,amount);

    uint256 userShareAfterDeposit = getShares(epochId, vault, to);
    uint256 totalSupplyAfterDeposit = getTotalSupply(epochId, vault);

    assert (amount > 0) => ((userShareAfterDeposit > userShareBeforeDeposit) && (totalSupplyAfterDeposit > totalSupplyBeforeDeposit) && (totalSupplyAfterDeposit == totalSupplyBeforeDeposit + amount)), "deposit amount > 0 should increase user share and total supply";
    assert (amount == 0) => (userShareAfterDeposit == userShareBeforeDeposit && totalSupplyAfterDeposit == totalSupplyBeforeDeposit), "amount = 0 means no increment for user share and total vault supply";

}

// variable transtition
// verified
rule user_share_and_total_supply_non_increasing_when_user_withdraws() {
    env e;

    uint256 epochId = currentEpoch();
    address vault;
    
    address from; 
    uint256 amount;

    uint256 userShareBeforeDeposit = getShares(epochId, vault, from);
    uint256 totalSupplyBeforeDeposit = getTotalSupply(epochId, vault);

    handleWithdrawal(e,vault,from,amount);

    uint256 userShareAfterDeposit = getShares(epochId, vault, from);
    uint256 totalSupplyAfterDeposit = getTotalSupply(epochId, vault);

  assert (amount > 0) => ((userShareAfterDeposit < userShareBeforeDeposit) && (totalSupplyAfterDeposit < totalSupplyBeforeDeposit) && (totalSupplyAfterDeposit == totalSupplyBeforeDeposit - amount)), "withdraw amount > 0 should decrease user share and total supply";
  assert (amount == 0) => ((userShareAfterDeposit == userShareBeforeDeposit) && (totalSupplyAfterDeposit == totalSupplyBeforeDeposit)), "amount = 0 means user share and total supply should be unaffected";

}

// variable transtition
// verified
rule user_share_and_total_supply_updated_when_users_transfers() {
    env e;

    uint256 epochId = currentEpoch();
    address vault;
    
    address from; 
    address to;
    uint256 amount;

    uint256 fromUserShareBeforeDeposit = getShares(epochId, vault, from);
    uint256 toUserShareBeforeDeposit = getShares(epochId, vault, to);
    uint256 totalSupplyBeforeDeposit = getTotalSupply(epochId, vault);

    handleTransfer(e,vault, from, to,amount);

    uint256 fromUserShareAfterDeposit = getShares(epochId, vault, from);
    uint256 toUserShareAfterDeposit = getShares(epochId, vault, to);
    uint256 totalSupplyAfterDeposit = getTotalSupply(epochId, vault);

    assert (amount == 0) => ((fromUserShareAfterDeposit == fromUserShareBeforeDeposit) && (toUserShareAfterDeposit == toUserShareBeforeDeposit)), "amount = 0 still values got updated";
    assert (amount > 0 && from == to) => ((fromUserShareAfterDeposit == fromUserShareBeforeDeposit) && (toUserShareAfterDeposit == toUserShareBeforeDeposit)), "from and to are same, no update";
    assert (amount > 0 && from != to) => ((fromUserShareAfterDeposit < fromUserShareBeforeDeposit) && (toUserShareAfterDeposit > toUserShareBeforeDeposit)), "should decrease from from-user and increase in to-user";
    assert (totalSupplyBeforeDeposit == totalSupplyAfterDeposit), "total supply must be same";
}

// unit test
// verified
rule notify_transfer_work_as_expected() {
     env e;

    uint256 epochId = currentEpoch();
    address vault;
    
    address from; 
    address to;
    uint256 amount;

    require vault == e.msg.sender;
    require epochId > 0;
    require from != 0 && to != 0;

    uint256 fromUserShareBeforeTransfer = getShares(epochId, vault, from);
    uint256 toUserShareBeforeTransfer = getShares(epochId, vault, to);
    uint256 totalSupplyBeforeTransfer = getTotalSupply(epochId, vault);

    require fromUserShareBeforeTransfer >= amount && toUserShareBeforeTransfer >= amount; 

    notifyTransfer(e, from, to, amount);

    uint256 fromUserShareAfterTransfer = getShares(epochId, vault, from);
    uint256 toUserShareAfterTransfer = getShares(epochId, vault, to);
    uint256 totalSupplyAfterTransfer = getTotalSupply(epochId, vault);


    assert (amount == 0) => ((fromUserShareBeforeTransfer == fromUserShareAfterTransfer) && (toUserShareAfterTransfer == toUserShareBeforeTransfer) && (totalSupplyAfterTransfer == totalSupplyBeforeTransfer)), "values changed even after amount = 0";
    assert (amount > 0 && (from == 0 && to != 0)) => ((toUserShareAfterTransfer > toUserShareBeforeTransfer) && (totalSupplyAfterTransfer > totalSupplyBeforeTransfer) && (totalSupplyAfterTransfer == totalSupplyBeforeTransfer + amount)), "to user share/total supply did not increase";
    assert (amount > 0 && (from != 0 && to == 0)) => ((fromUserShareAfterTransfer < fromUserShareBeforeTransfer) && (totalSupplyAfterTransfer < totalSupplyBeforeTransfer) && (totalSupplyAfterTransfer == totalSupplyBeforeTransfer - amount)), "from user share/total supply did not decrease";
    assert (amount > 0 && from != to) => (((fromUserShareAfterTransfer < fromUserShareBeforeTransfer) && (toUserShareAfterTransfer > toUserShareBeforeTransfer ))) && (totalSupplyBeforeTransfer == totalSupplyAfterTransfer), "values did nott update correctly";

}



