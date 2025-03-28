package net.postchain.gtx.extensions.vectordb

import com.google.common.io.Files
import com.google.gson.Gson
import net.postchain.base.BaseEContext
import net.postchain.base.data.PostgreSQLDatabaseAccess
import net.postchain.client.config.PostchainClientConfig
import net.postchain.client.impl.PostchainClientImpl
import net.postchain.client.request.EndpointPool
import net.postchain.d1.client.StandardChromiaClient
import net.postchain.gtv.GtvFactory.gtv
import org.junit.jupiter.api.Disabled
import org.junit.jupiter.api.Test
import java.io.File
import java.lang.Thread.sleep
import java.math.BigDecimal
import java.nio.charset.Charset
import java.sql.DriverManager
import java.sql.SQLException
import java.util.concurrent.BlockingQueue
import java.util.concurrent.LinkedBlockingQueue
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicLong
import kotlin.random.Random
import kotlin.time.measureTime

class VectorDbPerformance {

    private val gson = Gson()
        private val url = "jdbc:postgresql://172.17.0.1:5439/postchain?currentSchema=postchain0_c1" // Postchain sub node container
//    private val url = "jdbc:postgresql://localhost:5432/postchain?currentSchema=postchain0_c1" // PG container
//    private val url = "jdbc:postgresql://localhost:5438/postchain?currentSchema=postchain0_c1" // PG container - pgvector-scale
    private val user = "postchain"
    private val password = "postchain"
//    private val url = "jdbc:postgresql://localhost:5434/postchain?currentSchema=postchain0_c1" // PG container - pgvector-scale
//    private val user = "postgres"
//    private val password = "postgres"

    @Test
    @Disabled
    fun performance() {

        val dimensions = 768
        val maxNumOfThreads = 2
        val maxDistance = "0.1"
        val randomBoundary = 0.170631
        val testDurationMillis = 15_000L

        val insertTime = measureTime {
//            insertData(makeJsonlVectorProvider(dimensions, "/home/joh-nils/Downloads/0.jsonl"))
//            insertData(makeJsonlVectorProvider(dimensions, "/home/joh-nils/Downloads/100.jsonl"))
//            insertData(makeRandomVectorProvider(dimensions, 500_000, 1.0))
        }
        println("Data loaded in $insertTime")

        runQueries(maxNumOfThreads, testDurationMillis, restQuery(maxDistance) { vpRandomWithBoundaries(dimensions, randomBoundary) })
        runQueries(maxNumOfThreads, testDurationMillis, pqQuery(maxDistance) { vpRandomWithBoundaries(dimensions, randomBoundary) })
//        runQueries(maxNumOfThreads, testDurationMillis, restQuery(maxDistance, createExactVectors("/home/joh-nils/Downloads/0.jsonl", maxNumOfThreads * 10_000)))
//        runQueries(maxNumOfThreads, testDurationMillis, pqQuery(maxDistance, createExactVectors("/home/joh-nils/Downloads/0.jsonl", maxNumOfThreads * 10_000)))
    }

    private fun makeRandomVectorProvider(dimensions: Int, count: Long, boundary: Double? = null): (queue: BlockingQueue<String>) -> Unit {

        val ctx = BaseEContext(DriverManager.getConnection(url, user, password), 100, PostgreSQLDatabaseAccess())
        val vectorDbDatabaseOperations = VectorDbDatabaseOperations()
        vectorDbDatabaseOperations.initialize(ctx, VectorDbConfig(dimensions.toLong()))

        return { queue ->
            for (i in 1..count) {
                queue.add(getVector(dimensions, boundary))
            }

            println("${Thread.currentThread().name}: $count vectors generated, ${queue.size} items left in queue")
        }
    }

    private fun makeJsonlVectorProvider(dimensions: Int, file: String): (queue: BlockingQueue<String>) -> Unit {
        val titles = AtomicLong(0)
        val abstracts = AtomicLong(0)
        val ctx = BaseEContext(DriverManager.getConnection(url, user, password), 100, PostgreSQLDatabaseAccess())
        val vectorDbDatabaseOperations = VectorDbDatabaseOperations()
        vectorDbDatabaseOperations.initialize(ctx, VectorDbConfig(dimensions.toLong()))
        return { queue ->
            Files.readLines(File(file), Charset.defaultCharset()).forEach {
                val sf = gson.fromJson(it, Map::class.java)

                val titleEmbeddings = sf["title_embedding"]?.toString()
                if (titleEmbeddings != null) {
                    queue.put(titleEmbeddings)
                    titles.incrementAndGet()
                }
                val abstractEmbeddings = sf["abstract_embedding"]?.toString()
                if (abstractEmbeddings != null) {
                    queue.put(abstractEmbeddings)
                    abstracts.incrementAndGet()
                }

                if ((titles.get() + abstracts.get()) % 10_000 == 0L) {
                    println("${Thread.currentThread().name}: titles: $titles Abstracts: $abstracts")
                }
            }
            println("${Thread.currentThread().name}: EOF reached, ${queue.size} items left in queue")
        }
    }

    private fun pqQuery(maxDistance: String, vectorProvider: () -> String): (run: AtomicBoolean, requests: AtomicLong, hits: AtomicLong) -> Thread {
        return { run: AtomicBoolean, requests: AtomicLong, hits: AtomicLong ->
            Thread.ofVirtual()
                    .unstarted {
                        val ctx = BaseEContext(DriverManager.getConnection(url, user, password), 100, PostgreSQLDatabaseAccess())
                        val vectorDbDatabaseOperations = VectorDbDatabaseOperations()

                        while (run.get()) {
                            val result = vectorDbDatabaseOperations.queryClosestObjects(ctx, 0L, vectorProvider(), BigDecimal(maxDistance), 10)
                            requests.incrementAndGet()
                            if (result.asArray().isNotEmpty()) {
                                hits.incrementAndGet()
                            }
                        }

                        ctx.conn.close()
                    }
        }
    }

    private fun restQuery(maxDistance: String, vectorProvider: () -> String): (AtomicBoolean, AtomicLong, AtomicLong) -> Thread {
        val chromiaClient = StandardChromiaClient(EndpointPool.singleUrl("http://localhost:7740"))
        val brid = chromiaClient.getDirectoryChainClient().getBlockchainRID(100)
        val vc = PostchainClientImpl(PostchainClientConfig(
                blockchainRid = brid,
                chromiaClient.config.endpointPool
        ))
        return { run: AtomicBoolean, requests: AtomicLong, hits: AtomicLong ->
            Thread.ofVirtual()
                    .unstarted {
                        while (run.get()) {
                            val result = vc.query("query_closest_objects", gtv(mapOf(
                                    "context" to gtv(0),
                                    "q_vector" to gtv(vectorProvider()),
                                    "max_distance" to gtv(maxDistance),
                            )))
                            requests.incrementAndGet()
                            if (result.asArray().isNotEmpty()) {
                                hits.incrementAndGet()
                            }
                        }
                    }
        }
    }

    private fun runQueries(maxNumOfThreads: Int, millis: Long, threadProvider: (run: AtomicBoolean, requests: AtomicLong, hits: AtomicLong) -> Thread) {

        val threads = mutableListOf<Thread>()
        val requests = AtomicLong(0)
        val hits = AtomicLong(0)
        val run = AtomicBoolean(true)
        var lastTp = 0.0
        var noImprovement = 0

        println("Running queries with 1 to $maxNumOfThreads threads:")

        for (numOfThreads in 1..maxNumOfThreads step 1) {

            hits.set(0)
            requests.set(0)
            threads.clear()
            run.set(true)

            for (i in 1..numOfThreads) {
                threads.add(threadProvider(run, requests, hits))
            }

            val start = System.currentTimeMillis()
            threads.forEach { it.start() }

            sleep(millis)
            val tp = requests.get() / ((System.currentTimeMillis() - start) / 1000.0)
            print("$numOfThreads threads, requests: ${requests.get()}, Hits: ${hits.get()}, req/s: " + String.format("%.2f", tp))

            run.set(false)
            threads.forEach { it.join() }

            val improvement = tp / lastTp
            if (improvement < 0 || improvement <= 1.05) {

                println(", improvement: %.3f (no)".format(improvement))

                noImprovement++
                if (noImprovement >= 3) {
                    println(" -> No improvement for 3 following rounds, aborting")
//                    return
                }
            } else {
                println(", improvement: %.3f (yes)".format(improvement))
                noImprovement = 0
            }
            lastTp = tp
        }
    }

    private fun createExactVectors(file: String, count: Int): () -> String {

        println("Loading vectors from file: $file")

        val vectors = mutableListOf<String>()
        Files.readLines(File(file), Charset.defaultCharset()).subList(0, count).forEach {
            val sf = gson.fromJson(it, Map::class.java)

            val titleEmbeddings = sf["title_embedding"]?.toString()
            if (titleEmbeddings != null) {
                vectors.add(titleEmbeddings)
            }
            val abstractEmbeddings = sf["abstract_embedding"]?.toString()
            if (abstractEmbeddings != null) {
                vectors.add(abstractEmbeddings)
            }

            if (vectors.size % 2_000 == 0) {
                println("Vectors loaded: ${vectors.size}")
            }
        }

        println("Vectors loaded: ${vectors.size} (last)")

        val counter = AtomicInteger(0)

        return {
            var next = counter.incrementAndGet()
            if (next > count) {
                counter.set(0)
                next = 0
            }
            vectors[next]
        }
    }

    private fun vpRandom(dimensions: Int): String {
        return getVector(dimensions)
    }

    private fun vpRandomWithBoundaries(dimensions: Int, boundary: Double): String {
        return getVector(dimensions, boundary)
    }

    private fun insertData(vectorsProvider: (queue: BlockingQueue<String>) -> Unit) {

        val threads = mutableListOf<Thread>()
        val insertsPerCommit = 3_000L
        val inserts = AtomicLong(0)
        val queue: BlockingQueue<String> = LinkedBlockingQueue(10_000)
        val loading = AtomicBoolean(true)


        threads.add(Thread.ofVirtual()
                .name("L")
                .start {
                    vectorsProvider(queue)
                    println("${Thread.currentThread().name}: Data loaded, ${queue.size} items left in queue")
                    loading.set(false)
                })

        val sql = "INSERT INTO \"c100.sys.x.stored_vector\" (context, id, embedding) VALUES (0, ?, ?::vector)"
        for (i in 1..3) {
            threads.add(Thread.ofVirtual()
                    .name("T$i")
                    .start {
                        try {
                            DriverManager.getConnection(url, user, password).use { conn ->
                                // Disable auto-commit for better performance
                                conn.autoCommit = false

                                while (loading.get()) {

                                    try {
                                        var batchSize = 0L
                                        var start = System.currentTimeMillis()
                                        conn.prepareStatement(sql).use { pstmt ->
                                            while (true) {
                                                val poll = queue.poll(3_000, TimeUnit.MILLISECONDS)
                                                if (poll != null) {
                                                    pstmt.setLong(1, inserts.incrementAndGet())
                                                    pstmt.setString(2, poll)
                                                    pstmt.addBatch()
                                                    batchSize++
                                                }

                                                if (batchSize >= insertsPerCommit || poll == null) {

                                                    pstmt.executeBatch()
                                                    conn.commit()

                                                    println("${Thread.currentThread().name}: Inserted $batchSize vectors items in ${System.currentTimeMillis() - start} ms - total inserts: ${inserts.get()}")
                                                    batchSize = 0L
                                                    start = System.currentTimeMillis()

                                                    if (poll == null) {
                                                        println("${Thread.currentThread().name}: No more items, queue size: ${queue.size}")
                                                        break
                                                    }
                                                }
                                            }
                                        }
                                    } catch (e: Exception) {
                                        e.printStackTrace()
                                    }
                                }
                            }
                        } catch (e: SQLException) {
                            e.printStackTrace()
                        }
                    })
        }

        println("Joining threads...")

        threads.forEach { it.join() }

        println("Import done")
    }

    fun getVector(dimensions: Int, boundary: Double? = null): String {
        val decimals = mutableListOf<Float>()
        for (i in 1..dimensions) {
            if (boundary == null) {
                decimals.add(Random.nextFloat())
            } else {
                decimals.add(Random.nextDouble(-1 * boundary, boundary).toFloat())
            }
        }
        return decimals.joinToString(",", "[", "]")
    }
}

