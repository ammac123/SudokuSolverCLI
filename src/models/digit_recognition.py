import easyocr
import numpy as np
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="torch.utils.data")

_READER = easyocr.Reader(
    ['en'], 
    recog_network="english_g2",
    model_storage_directory="src/models",
    user_network_directory="src/models",
    verbose=False,
    download_enabled=False,
    cudnn_benchmark=True,
    )

def read_digit(cell, reader: easyocr.Reader, debug=False):
    try:
        reader.verbose = debug
        res = reader.readtext(
            cell, 
            allowlist="123456789",
            text_threshold=0.5,
            min_size=10,
            max_candidates=1,
            detail=0
        )
        if res == []:
            return None
        text = res[0] #type: ignore
        digit = "".join((d for d in text if d.isdigit()))[0]
        return int(digit) or None
    except ValueError:
        return None


def extract_grid(cells: list[np.ndarray], reader: easyocr.Reader = _READER, debug=False) -> list[list[int]]:
    digits = [read_digit(c, reader, debug) for c in cells]
    return [digits[r*9:(r+1)*9] for r in range(9)] #type: ignore


def process_cells(cells: list[np.ndarray], reader: easyocr.Reader, cell_size=50, debug=False):
    reader.verbose = debug
    res = reader.readtext_batched(
        cells,
        batch_size=1,
        allowlist="123456789",
        text_threshold=0.3,
        min_size=10,
        n_height=cell_size,
        n_width=cell_size,
        decoder='beamsearch',
    )
    if res == []:
        raise ValueError("Could not read puzzle grid")
    return res


def generate_puzzle_from_cells(cells: list[np.ndarray], reader: easyocr.Reader = _READER, cell_size = 50, debug = False):
    results = process_cells(cells, reader, cell_size, debug)
    puzzle_list = [[None]*9 for _ in range(9)]
    for idx, res in enumerate(results):
        if not res:
            continue
        row, col = idx % 9, (idx // 9) % 9
        _, digit, p = max(res, key=lambda x: x[2])
        if p < 0.3:
            continue
        try:
            d = int(digit[0])
            puzzle_list[col][row] = d # type: ignore
        except:
            continue
    return puzzle_list


def draw_digit_boxes(grid_img: np.ndarray, cells: list[np.ndarray], reader: easyocr.Reader = _READER, cell_size=50, debug=False):
    import cv2
    results = process_cells(cells, reader, cell_size=cell_size, debug=debug)
    out = grid_img.copy()
    if out.ndim == 2:
        out = cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)
    for idx, res in enumerate(results):
        if not res:
            continue
        row, col = idx % 9, (idx // 9) % 9
        for bbox, text, prob in res:
            pts = np.array(bbox, dtype="int32").reshape(-1, 1, 2) # type: ignore
            pts[:, 0, 0] += row*cell_size
            pts[:, 0, 1] += col*cell_size
            cv2.polylines(out, [pts], isClosed=True, color=(0, 255, 0), thickness=2) #type: ignore
            x, y = pts[0, 0]
            cv2.putText(out, f"{text} ({prob:.2f})", (int(x), int(y)-5), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
        
    return out



def main():
    pass

if __name__=="__main__":
    main()