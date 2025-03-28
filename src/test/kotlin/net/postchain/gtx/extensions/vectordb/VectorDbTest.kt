package net.postchain.gtx.extensions.vectordb

import assertk.assertThat
import assertk.assertions.hasSize
import assertk.assertions.isEqualTo
import net.postchain.devtools.IntegrationTestSetup
import net.postchain.devtools.PostchainTestNode.Companion.DEFAULT_CHAIN_IID
import net.postchain.gtv.GtvFactory.gtv
import org.awaitility.Awaitility.await
import org.awaitility.Duration
import org.junit.jupiter.api.Test

class VectorDbIT : IntegrationTestSetup() {

    init {
        configOverrides.setProperty("messaging.port", 0)
    }

    @Test
    fun `basics - add, query and delete`() {

        val node = createNodes(1, "/net/postchain/gtx/extensions/vectordb/vector_example_3d.xml")[0]
        val engine = node.getBlockchainInstance().blockchainEngine

        addMessage(engine, "hello", "[1, 2, 3]")
        buildBlock(DEFAULT_CHAIN_IID)

        val queryResults = queryClosestObjectsGetStrings(engine, 0, "[1, 2, 3]", 1.0, 1, "get_messages")

        assertThat(queryResults).hasSize(1)
        assertThat(queryResults[0]).isEqualTo("hello")

        assertThat(getVectors(engine, DEFAULT_CHAIN_IID)).hasSize(1)

        deleteMessage(engine, "hello")
        buildBlock(DEFAULT_CHAIN_IID)
        await().atMost(Duration.TEN_SECONDS).untilAsserted {
            assertThat(getVectors(engine, DEFAULT_CHAIN_IID)).hasSize(0)
        }
    }

    @Test
    fun `query - different limitations`() {
        val node = createNodes(1, "/net/postchain/gtx/extensions/vectordb/vector_example_3d.xml")[0]
        val engine = node.getBlockchainInstance().blockchainEngine

        addMessage(engine, "alpha", "[1, 2, 3]")
        addMessage(engine, "beta", "[1, 4, 3]")
        addMessage(engine, "charlie", "[7, 4, 3]")
        addMessage(engine, "dave", "[9, 8, 4]")
        addMessage(engine, "eve", "[2, 3, 7]")
        buildBlock(DEFAULT_CHAIN_IID)

        assertThat(
                queryClosestObjectsGetStrings(engine, 0, "[1, 2, 3]", 1.0, 3, "get_messages")
        ).isEqualTo(listOf("alpha", "eve", "beta"))

        assertThat(
                queryClosestObjectsGetStrings(engine, 0, "[1, 2, 3]", 0.02, 3, "get_messages")
        ).isEqualTo(listOf("alpha", "eve"))
    }

    @Test
    fun `query - with distance`() {
        val node = createNodes(1, "/net/postchain/gtx/extensions/vectordb/vector_example_3d.xml")[0]
        val engine = node.getBlockchainInstance().blockchainEngine

        addMessage(engine, "alpha", "[1, 2, 3]")
        addMessage(engine, "beta", "[1, 4, 3]")
        addMessage(engine, "charlie", "[7, 4, 3]")
        addMessage(engine, "dave", "[9, 8, 4]")
        addMessage(engine, "eve", "[2, 3, 7]")
        buildBlock(DEFAULT_CHAIN_IID)

        assertThat(
                queryClosestObjectsGetTextAndDistance(engine, 0, "[1, 2, 3]", 1.0, 3, "get_messages_with_distance")
        ).isEqualTo(listOf(
                mapOf("text" to "alpha", "distance" to "0"),
                mapOf("text" to "eve", "distance"  to "0.015675861711910488"),
                mapOf("text" to "beta", "distance"  to "0.056543646950273474")
        ))

        assertThat(
                queryClosestObjectsGetTextAndDistance(engine, 0, "[1, 2, 3]", 0.02, 3, "get_messages_with_distance")
        ).isEqualTo(listOf(
                mapOf("text" to "alpha", "distance" to "0"),
                mapOf("text" to "eve", "distance"  to "0.015675861711910488"),
        ))
    }

    @Test
    fun `query - with custom template arguments`() {
        val node = createNodes(1, "/net/postchain/gtx/extensions/vectordb/vector_example_3d.xml")[0]
        val engine = node.getBlockchainInstance().blockchainEngine

        addMessage(engine, "alpha", "[1, 2, 3]")
        addMessage(engine, "beta", "[1, 4, 3]")
        addMessage(engine, "charlie", "[7, 4, 3]")
        addMessage(engine, "dave", "[9, 8, 4]")
        addMessage(engine, "eve", "[2, 3, 7]")
        buildBlock(DEFAULT_CHAIN_IID)

        assertThat(
                queryClosestObjects(engine, VECTOR_DB_QUERY_CLOSEST_OBJECTS, 0, "[1, 2, 3]", 1.0, 3,
                        buildQueryTemplateOrNull("get_messages_with_filter",
                            gtv(mapOf(
                                "text_filter" to gtv("v"),
                            ))
                        )
                ).asArray().map { it.asString() }
        ).isEqualTo(listOf("eve"))
    }

    @Test
    fun `query - without query template`() {
        val node = createNodes(1, "/net/postchain/gtx/extensions/vectordb/vector_example_3d.xml")[0]
        val engine = node.getBlockchainInstance().blockchainEngine

        addMessage(engine, "alpha", "[1, 2, 3]")
        addMessage(engine, "beta", "[1, 4, 3]")
        buildBlock(DEFAULT_CHAIN_IID)

        assertThat(
                queryClosestObjectsGetIdAndDistance(engine, 0, "[1, 2, 3]", 0.0, 1)
        ).isEqualTo(listOf(
                mapOf(
                        "id" to 1L,
                        "distance" to "0"
                )
        ))
    }

    @Test
    fun `test add and delete`() {
        val node = createNodes(1, "/net/postchain/gtx/extensions/vectordb/vector_example_3d.xml")[0]
        val engine = node.getBlockchainInstance().blockchainEngine

        addMessage(engine, "alpha", "[1, 2, 3]")
        addMessage(engine, "beta", "[1, 2, 3]")
        addMessage(engine, "charlie", "[1, 2, 3]")
        buildBlock(DEFAULT_CHAIN_IID)

        assertThat(getVectors(engine, DEFAULT_CHAIN_IID)).hasSize(3)

        deleteMessage(engine, "beta")
        buildBlock(DEFAULT_CHAIN_IID)
        await().atMost(Duration.TEN_SECONDS).untilAsserted {
            assertThat(getVectors(engine, DEFAULT_CHAIN_IID)).hasSize(2)
        }

        addMessage(engine, "delta", "[1, 2, 3]")
        deleteMessage(engine, "charlie")
        buildBlock(DEFAULT_CHAIN_IID)
        await().atMost(Duration.TEN_SECONDS).untilAsserted {
            assertThat(getVectors(engine, DEFAULT_CHAIN_IID)).hasSize(2)
        }

        addMessage(engine, "dave", "[1, 2, 3]")
        deleteMessage(engine, "dave")
        deleteMessage(engine, "alpha")
        buildBlock(DEFAULT_CHAIN_IID)
        await().atMost(Duration.TEN_SECONDS).untilAsserted {
            assertThat(getVectors(engine, DEFAULT_CHAIN_IID)).hasSize(1)
        }
    }
}
