package net.postchain.gtx.extensions.vectordb

import net.postchain.gtv.mapper.Name

data class VectorDbConfig(
        /** Number of dimensions of the vectors */
        @Name("dimensions")
        val dimensions: Long,
)