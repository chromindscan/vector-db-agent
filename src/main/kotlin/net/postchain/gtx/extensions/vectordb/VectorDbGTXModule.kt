package net.postchain.gtx.extensions.vectordb

import mu.KLogging
import net.postchain.PostchainContext
import net.postchain.base.BaseBlockBuilderExtension
import net.postchain.common.exception.UserMistake
import net.postchain.core.BlockchainConfiguration
import net.postchain.core.EContext
import net.postchain.gtv.Gtv
import net.postchain.gtv.GtvFactory.gtv
import net.postchain.gtv.mapper.toObject
import net.postchain.gtx.GTXModule
import net.postchain.gtx.GTXModuleAware
import net.postchain.gtx.PostchainContextAware
import net.postchain.gtx.SimpleGTXModule
import net.postchain.gtx.special.GTXSpecialTxExtension
import java.math.BigDecimal

const val VECTOR_DB_QUERY_CLOSEST_OBJECTS = "query_closest_objects"

class VectorDbGTXModuleContext(
        val databaseOperations: VectorDbDatabaseOperations,
) {
    lateinit var module: GTXModule
}

class VectorDbGTXModule(
        private val databaseOperations: VectorDbDatabaseOperations = VectorDbDatabaseOperations()
) : SimpleGTXModule<VectorDbGTXModuleContext>(
        VectorDbGTXModuleContext(databaseOperations), mapOf(), mapOf(
        VECTOR_DB_QUERY_CLOSEST_OBJECTS to Companion::queryClosestObjects,
    )
), PostchainContextAware {

    private var chainId: Long? = null

    companion object : KLogging() {
        fun queryClosestObjects(moduleContext: VectorDbGTXModuleContext, ctx: EContext, args: Gtv): Gtv {
            val context = args["context"]?.asInteger() ?: throw UserMistake("No context argument supplied")
            val vectorQuery = args["q_vector"]?.asString() ?: throw UserMistake("No q_vector argument supplied")
            val maxDistance = BigDecimal(args["max_distance"]?.asString() ?: throw UserMistake("No max_distance argument supplied"))
            val maxVectors = args["max_vectors"]?.asInteger() ?: 10L
            val queryTemplate = args["query_template"]?.asDict()

            val vectorResult = moduleContext.databaseOperations.queryClosestObjects(ctx, context, vectorQuery, maxDistance, maxVectors)

            return if (queryTemplate == null) {
                vectorResult
            } else {
                val queryTemplateType = queryTemplate["type"]?.asString() ?: throw UserMistake("No type argument supplied to query_template")
                val queryTemplateArgs = queryTemplate["args"]?.asDict() ?: mapOf()
                return moduleContext.module.query(ctx, queryTemplateType,
                        gtv(mapOf("closest_results" to vectorResult) + queryTemplateArgs))
            }
        }
    }

    override fun initializeContext(configuration: BlockchainConfiguration, postchainContext: PostchainContext) {
        conf.module = (configuration as GTXModuleAware).module

        val vectorDbConfig = configuration.rawConfig["vector_db_extension"]?.toObject<VectorDbConfig>()
                ?: throw UserMistake("No vector db extension config present")

        if (chainId != null) {

            val ctx = postchainContext.blockBuilderStorage.openWriteConnection(chainId!!)
            try{
                databaseOperations.initialize(ctx, vectorDbConfig)
            } finally {
                postchainContext.blockBuilderStorage.closeWriteConnection(ctx, true)
            }
        }
    }

    override fun initializeDB(ctx: EContext) {
        chainId = ctx.chainID
    }

    override fun getSpecialTxExtensions() = emptyList<GTXSpecialTxExtension>()

    override fun makeBlockBuilderExtensions(): List<BaseBlockBuilderExtension>  {
        return listOf(VectorDbEventProcessor(databaseOperations))
    }
}
