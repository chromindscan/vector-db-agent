package net.postchain.gtx.extensions.vectordb

import net.postchain.base.data.DatabaseAccess
import net.postchain.concurrent.util.get
import net.postchain.core.BlockchainEngine
import net.postchain.gtv.Gtv
import net.postchain.gtv.GtvDictionary
import net.postchain.gtv.GtvFactory.gtv
import net.postchain.gtx.Gtx
import net.postchain.gtx.GtxBody
import net.postchain.gtx.GtxOp
import net.postchain.gtx.extensions.vectordb.VectorDbDatabaseOperations.Companion.VECTOR_DB_COLUMN_CONTEXT
import net.postchain.gtx.extensions.vectordb.VectorDbDatabaseOperations.Companion.VECTOR_DB_COLUMN_EMBEDDING
import net.postchain.gtx.extensions.vectordb.VectorDbDatabaseOperations.Companion.VECTOR_DB_COLUMN_ID

fun getVectors(engine: BlockchainEngine, chainId: Long): List<Vector> {
    val ctx = engine.blockBuilderStorage.openReadConnection(chainId)
    try {
        DatabaseAccess.of(ctx).apply {
            val tableName = getVectorDbTableName(ctx)
            val rs = ctx.conn.createStatement().executeQuery("SELECT $VECTOR_DB_COLUMN_CONTEXT, $VECTOR_DB_COLUMN_ID, $VECTOR_DB_COLUMN_EMBEDDING FROM $tableName")
            val vectors = mutableListOf<Vector>()
            while (rs.next()) {
                vectors.add(Vector(rs.getLong(1), rs.getLong(2), rs.getString(3)))
            }
            return vectors
        }
    } finally {
        engine.blockBuilderStorage.closeReadConnection(ctx)
    }
}

fun queryClosestObjectsGetStrings(engine: BlockchainEngine, context: Long, vector: String, maxDistance: Double, maxVectors: Long, queryTemplateType: String? = null): List<String> {
    return queryClosestObjects(engine, VECTOR_DB_QUERY_CLOSEST_OBJECTS, context, vector, maxDistance, maxVectors, buildQueryTemplateOrNull(queryTemplateType))
            .asArray().map { it.asString() }
}

fun queryClosestObjectsGetIdAndDistance(engine: BlockchainEngine, context: Long, vector: String, maxDistance: Double, maxVectors: Long, queryTemplateType: String? = null): List<Map<String, Any>> {
    return queryClosestObjects(engine, VECTOR_DB_QUERY_CLOSEST_OBJECTS, context, vector, maxDistance, maxVectors, buildQueryTemplateOrNull(queryTemplateType))
            .asArray()
            .map { mapOf(
                    "id" to it.asDict()["id"]!!.asInteger(),
                    "distance" to it.asDict()["distance"]!!.asString()
            )}
}

fun queryClosestObjectsGetTextAndDistance(engine: BlockchainEngine, context: Long, vector: String, maxDistance: Double, maxVectors: Long, queryTemplateType: String? = null): List<Map<String, String>> {
    return queryClosestObjects(engine, VECTOR_DB_QUERY_CLOSEST_OBJECTS, context, vector, maxDistance, maxVectors, buildQueryTemplateOrNull(queryTemplateType)).asArray()
            .map { mapOf(
                    "text" to it.asDict()["text"]!!.asString(),
                    "distance" to it.asDict()["distance"]!!.asString()
            )}
}

fun queryClosestObjects(engine: BlockchainEngine, queryName: String, context: Long, vector: String, maxDistance: Double, maxVectors: Long, queryTemplate: GtvDictionary? = null): Gtv {
    val args = mutableListOf<Pair<String, Gtv>>(
            "context" to gtv(context),
            "q_vector" to gtv(vector),
            "max_distance" to gtv(maxDistance.toString()),
            "max_vectors" to gtv(maxVectors),
    )
    if (queryTemplate != null) {
        args.add("query_template" to queryTemplate)
    }
    return engine.getBlockQueries().query(queryName, gtv(mapOf(*args.toTypedArray()))).get()
}

fun buildQueryTemplateOrNull(type: String?, args: Gtv? = null): GtvDictionary? {
    if (type != null) {
        val dict: MutableMap<String, Gtv> = mutableMapOf(
                "type" to gtv(type),
        )
        if (args != null) {
            dict += mapOf("args" to args)
        }
        return gtv(dict)
    }
    return null
}

fun addMessage(engine: BlockchainEngine, message: String, vector: String) {
    val op = GtxOp("add_message", gtv(message), gtv(vector))
    val tx = engine.getConfiguration().getTransactionFactory().decodeTransaction(
            Gtx(GtxBody(engine.getConfiguration().blockchainRid, listOf(op), listOf()), listOf()).encode()
    )
    engine.getTransactionQueue().enqueue(tx)
}

fun deleteMessage(engine: BlockchainEngine, message: String) {
    val op = GtxOp("delete_message", gtv(message))
    val tx = engine.getConfiguration().getTransactionFactory().decodeTransaction(
            Gtx(GtxBody(engine.getConfiguration().blockchainRid, listOf(op), listOf()), listOf()).encode()
    )
    engine.getTransactionQueue().enqueue(tx)
}

data class Vector(val context: Long, val id: Long, val embedding: String)
