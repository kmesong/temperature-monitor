// Seven Segment OCR Logic

const OCR = {
    digitMap: {
        0x3F: '0', 0x06: '1', 0x5B: '2', 0x4F: '3', 0x66: '4',
        0x6D: '5', 0x7D: '6', 0x07: '7', 0x7F: '8', 0x6F: '9',
        0x40: '-', 0x77: 'A', 0x7C: 'b', 0x39: 'C', 0x5E: 'd', 
        0x79: 'E', 0x71: 'F'
    },

    recognize(imageData) {
        const { width, height, data } = imageData;
        const matrix = new Uint8Array(width * height);
        
        // Binarize
        for (let i = 0; i < width * height; i++) {
            matrix[i] = data[i * 4] > 128 ? 1 : 0;
        }

        const blobs = this.findBlobs(matrix, width, height);
        let result = "";
        
        blobs.forEach(blob => {
            const ratio = blob.w / blob.h;
            
            // Heuristic Classification: Dot vs Minus vs Digit
            if (blob.h < height * 0.4) {
                 if (blob.y > height * 0.6) {
                     result += ".";
                 } else {
                     result += "-";
                 }
            } else {
                 const char = this.scanSegments(blob, matrix, width);
                 result += char;
            }
        });

        return { text: result, blobs };
    },

    findBlobs(matrix, width, height) {
        const blobs = [];
        let inSegment = false;
        let startX = 0;
        const colSums = new Uint32Array(width);
        
        for (let x = 0; x < width; x++) {
            for (let y = 0; y < height; y++) matrix[y * width + x] && colSums[x]++;
        }

        for (let x = 0; x < width; x++) {
            if (colSums[x] > 0) {
                if (!inSegment) { inSegment = true; startX = x; }
            } else {
                if (inSegment) {
                    inSegment = false;
                    blobs.push(this.getBlobRect(matrix, width, height, startX, x - 1));
                }
            }
        }
        if (inSegment) blobs.push(this.getBlobRect(matrix, width, height, startX, width - 1));
        
        // Filter out noise (very small specks)
        return blobs.filter(b => b.w > 2 && b.h > 5); 
    },

    getBlobRect(matrix, width, height, startX, endX) {
        let minY = height, maxY = 0;
        for (let x = startX; x <= endX; x++) {
            for (let y = 0; y < height; y++) {
                if (matrix[y * width + x]) {
                    if (y < minY) minY = y;
                    if (y > maxY) maxY = y;
                }
            }
        }
        return { x: startX, y: minY, w: endX - startX + 1, h: maxY - minY + 1 };
    },

    scanSegments(blob, matrix, globalWidth) {
        const { x, y, w, h } = blob;
        
        // A: Top, B: Top-Right, C: Bot-Right, D: Bottom, E: Bot-Left, F: Top-Left, G: Mid
        const segments = [
            { id: 'A', u: 0.5, v: 0.15 },
            { id: 'B', u: 0.85, v: 0.25 },
            { id: 'C', u: 0.85, v: 0.75 },
            { id: 'D', u: 0.5, v: 0.85 },
            { id: 'E', u: 0.15, v: 0.75 },
            { id: 'F', u: 0.15, v: 0.25 },
            { id: 'G', u: 0.5, v: 0.5 }
        ];

        let signature = 0;
        
        segments.forEach((seg, index) => {
            const sx = Math.floor(x + w * seg.u);
            const sy = Math.floor(y + h * seg.v);
            
            let onPixels = 0;
            // 3x3 sampling
            for(let dy=-1; dy<=1; dy++) {
                for(let dx=-1; dx<=1; dx++) {
                    const idx = (sy + dy) * globalWidth + (sx + dx);
                    if (matrix[idx]) onPixels++;
                }
            }
            
            if (onPixels > 2) {
                signature |= (1 << index); 
            }
        });

        return this.digitMap[signature] || '?';
    }
};
