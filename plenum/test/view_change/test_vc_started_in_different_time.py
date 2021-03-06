import pytest

from plenum.test.helper import sdk_send_random_and_check, assertExp
from plenum.test.node_catchup.helper import ensure_all_nodes_have_same_data
from plenum.test.view_change.helper import restart_node, nodes_received_ic
from stp_core.loop.eventually import eventually

TestRunningTimeLimitSec = 150


@pytest.fixture(scope="module")
def tconf(tconf):
    old_val = tconf.ToleratePrimaryDisconnection
    tconf.ToleratePrimaryDisconnection = 1000
    yield tconf
    tconf.ToleratePrimaryDisconnection = old_val


def test_vc_started_in_different_time(looper, txnPoolNodeSet,
                                                   sdk_wallet_client, sdk_pool_handle,
                                                   tconf, tdir, allPluginsPath):

    alpha, beta, gamma, delta = txnPoolNodeSet

    # Delta and Gamma send InstanceChange for all nodes.
    for node in [gamma, delta]:
        node.view_changer.on_master_degradation()
        looper.run(
            eventually(nodes_received_ic, txnPoolNodeSet, node, 1))

    # Restart Alpha, Beta, Gamma
    for node in [alpha, beta, gamma]:
        restart_node(looper, txnPoolNodeSet, node, tconf, tdir, allPluginsPath)
    alpha, beta, gamma, delta = txnPoolNodeSet

    # Send InstanceChange from Beta for all nodes
    beta.view_changer.on_master_degradation()

    # Ensure that pool is still functional
    sdk_send_random_and_check(looper, txnPoolNodeSet,
                              sdk_pool_handle, sdk_wallet_client, 1)

    # Restart Alpha, Beta
    for i, node in enumerate([alpha, beta]):
        restart_node(looper, txnPoolNodeSet, node, tconf, tdir,
                     allPluginsPath, wait_node_data_equality=False)
    alpha, beta, gamma, delta = txnPoolNodeSet

    # Alpha, Gamma send InstanceChange for all nodes.
    for node in [alpha, gamma]:
        node.view_changer.on_master_degradation()

    # Ensure that pool is still functional
    sdk_send_random_and_check(looper, txnPoolNodeSet,
                              sdk_pool_handle, sdk_wallet_client, 1)
    ensure_all_nodes_have_same_data(looper, txnPoolNodeSet)
