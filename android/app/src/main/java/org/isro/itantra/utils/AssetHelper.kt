package org.isro.itantra.utils

import android.content.Context
import java.io.File
import java.io.FileOutputStream

object AssetHelper {
    fun copyAssetsToCache(context: Context, assetFolder: String, destFolder: File) {
        if (!destFolder.exists()) {
            destFolder.mkdirs()
        }
        val assets = context.assets.list(assetFolder) ?: return
        for (asset in assets) {
            val assetPath = if (assetFolder.isEmpty()) asset else "$assetFolder/$asset"
            val destFile = File(destFolder, asset)
            
            // Check if it's a directory
            val subAssets = context.assets.list(assetPath)
            if (subAssets != null && subAssets.isNotEmpty()) {
                copyAssetsToCache(context, assetPath, destFile)
            } else {
                if (!destFile.exists()) {
                    context.assets.open(assetPath).use { inputStream ->
                        FileOutputStream(destFile).use { outputStream ->
                            inputStream.copyTo(outputStream)
                        }
                    }
                }
            }
        }
    }
}

