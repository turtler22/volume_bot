// tokenTracker.js
const { Connection, PublicKey } = require('@solana/web3.js');
const { TokenListProvider } = require('@solana/spl-token-registry');

class SolanaTokenTracker {
    constructor(config = {}) {
        this.connection = new Connection(
            config.rpcUrl || 'https://api.mainnet-beta.solana.com'
        );
        this.checkInterval = config.checkInterval || 300000; // 5 minutes in milliseconds
        this.knownTokens = new Set();
        this.lastCheckTime = Date.now();
        
        this.onNewToken = config.onNewToken || ((token) => {
            console.log('\n🪙 New token detected:', {
                mint: token.mint,
                timestamp: token.timestamp,
                blockTime: token.blockTime,
                slot: token.slot
            });
        });
    }

    async initialize() {
        console.log('📋 Initializing token tracker...');
        console.log('🔄 Loading existing token list...');
        
        // Get existing tokens from token registry
        const tokens = await new TokenListProvider().resolve();
        const tokenList = tokens.filterByClusterSlug('mainnet-beta').getList();
        tokenList.forEach(token => {
            this.knownTokens.add(token.address);
        });
        
        console.log(`✅ Loaded ${this.knownTokens.size} existing tokens`);
    }

    async trackNewTokens() {
        try {
            const currentTime = Date.now();
            const newTokens = [];

            // Get current slot
            const currentSlot = await this.connection.getSlot();
            console.log(`\n🔍 Scanning blocks...`);
            console.log(`Current slot: ${currentSlot}`);

            // Get recent blocks
            const startSlot = currentSlot - 100;
            console.log(`Checking slots ${startSlot} to ${currentSlot}`);
            const blocks = await this.connection.getBlocks(startSlot, currentSlot);
            
            console.log(`📦 Found ${blocks.length} blocks to analyze`);

            for (const block of blocks) {
                process.stdout.write(`\r⚡ Analyzing block ${block}...`);
                const blockInfo = await this.connection.getBlock(block, {
                    maxSupportedTransactionVersion: 0
                });
                if (!blockInfo) continue;

                for (const tx of blockInfo.transactions) {
                    if (!tx.meta || !tx.transaction) continue;

                    // Look for token creation instructions
                    const createTokenInstr = tx.transaction.message.instructions.find(
                        instr => {
                            try {
                                return instr && 
                                       instr.programId && 
                                       instr.programId.equals(new PublicKey('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'));
                            } catch (e) {
                                return false;
                            }
                        }
                    );

                    if (createTokenInstr && createTokenInstr.accounts && createTokenInstr.accounts[0]) {
                        const tokenMint = createTokenInstr.accounts[0].toBase58();
                        
                        // Check if this is a new token
                        if (!this.knownTokens.has(tokenMint)) {
                            newTokens.push({
                                mint: tokenMint,
                                timestamp: new Date(currentTime).toISOString(),
                                blockTime: blockInfo.blockTime,
                                slot: block
                            });
                            this.knownTokens.add(tokenMint);
                        }
                    }
                }
            }

            console.log(`\n✨ Scan complete!`);
            if (newTokens.length > 0) {
                console.log(`Found ${newTokens.length} new tokens`);
            } else {
                console.log('No new tokens found in this scan');
            }

            this.lastCheckTime = currentTime;
            return newTokens;
        } catch (error) {
            console.error('❌ Error tracking new tokens:', error);
            return [];
        }
    }

    async start() {
        console.log(`
🚀 Starting token tracker
- Check interval: ${this.checkInterval / 1000} seconds
- RPC URL: ${this.connection.rpcEndpoint}
`);

        await this.initialize();
        
        console.log('\n⏱️  Starting periodic checks...');
        
        setInterval(async () => {
            console.log('\n------------------------------------------');
            console.log(`🔄 Starting new scan at ${new Date().toISOString()}`);
            const newTokens = await this.trackNewTokens();
            newTokens.forEach(this.onNewToken);
        }, this.checkInterval);
    }
}

async function main() {
    const tracker = new SolanaTokenTracker({
        checkInterval: 60000, // Check every 1 minute
        onNewToken: (token) => {
            console.log(`
🎯 Token Details:
Mint Address: ${token.mint}
Block: ${token.slot}
Block Time: ${new Date(token.blockTime * 1000).toISOString()}
Detection Time: ${token.timestamp}
            `);
        }
    });
    
    try {
        await tracker.start();
    } catch (error) {
        console.error('❌ Failed to start token tracker:', error);
    }
}

main().catch(console.error);