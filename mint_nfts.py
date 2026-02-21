import os
import subprocess

uris = {
    "cluster_gaps": "https://gateway.pinata.cloud/ipfs/bafkreiaozmzhohbubvwsn3qkx6h7kxchszwawamjkehxhzq5ofa5y2ouei",
    "double_neglect_scatter": "https://gateway.pinata.cloud/ipfs/bafkreial62mpyuq2m43p7duzyjcymp5r26wfppiu2vcxk3yebccmrrxq6e",
    "efficiency_scatter": "https://gateway.pinata.cloud/ipfs/bafkreigsfgw7szapxmnnrt6xcrvfkdlh2lh2xi65drkn3es4cnp4jshnnq",
    "funding_forecast": "https://gateway.pinata.cloud/ipfs/bafkreigp3xhdgwgmumdhfysemvk36n3rpwqsace6p32d7tsbtdwmlwnhle",
    "top_10_crises": "https://gateway.pinata.cloud/ipfs/bafkreie3ptak7fzwofg77wfpqiow5feg565sm34ouxqzyzkk43hlll4tj4",
    "world_map": "https://gateway.pinata.cloud/ipfs/bafkreigdwsdh5yx2pbgo55xrxglryc3d5p77bf4rxcodp5cgiktrjsyfve"
}

print("Starting the minting process...\n" + "="*40)

for name, uri in uris.items():
    print(f"Minting: {name}")
    
    # 1. Create the base token WITH the metadata pointer enabled
    command_create = "spl-token create-token --program-2022 --decimals 0 --enable-metadata"
    token_output = subprocess.getoutput(command_create)
    
    # Extract the new token address from the CLI output
    try:
        token_address = token_output.split("Creating token ")[1].split()[0]
        print(f"  Token ID: {token_address}")
    except IndexError:
        print(f"  Error creating token for {name}. Output: {token_output}")
        continue
    
    # 2. Bind your Pinata IPFS metadata to the token (This will work now!)
    os.system(f"spl-token initialize-metadata {token_address} '{name}' 'CRISIS' '{uri}'")
    
    # 3. Create an account in your wallet to hold the token
    os.system(f"spl-token create-account {token_address}")
    
    # 4. Mint exactly 1 token to your wallet (making it an NFT)
    os.system(f"spl-token mint {token_address} 1")
    
    # 5. Lock the mint so no more can ever be created
    os.system(f"spl-token authorize {token_address} mint --disable")

    print(f"Finished {name}\n" + "-"*40)