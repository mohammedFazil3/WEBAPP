# preprocessing/keystroke_processor.py

import pandas as pd
import numpy as np
import re
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

def standardize_keystrokes(df):
    """Standardize keystroke labels to ensure consistency."""
    df["Key Stroke"] = df["Key Stroke"].str.replace('^Key.alt_gr$', 'Key.alt_r', regex=True)
    df["Key Stroke"] = df["Key Stroke"].str.replace('^Key.shift$', 'Key.shift_l', regex=True)
    df["Key Stroke"] = df["Key Stroke"].str.replace('^Key.cmd$', 'Key.cmd_l', regex=True)
    return df

def standardize_windows_keystrokes(df):
    """
    Standardizes Windows keystrokes by:
    1. Mapping special Ctrl key sequences.
    2. Combining multi-key shortcuts into a single row.
    """
    # Ctrl key mappings (special character codes)
    ctrl_key_mapping = {
        "'\\x01'": "Ctrl + A", "'\\x02'": "Ctrl + B", "'\\x03'": "Ctrl + C",
        "'\\x04'": "Ctrl + D", "'\\x05'": "Ctrl + E", "'\\x06'": "Ctrl + F",
        "'\\x07'": "Ctrl + G", "'\\x08'": "Ctrl + H", "'\\x09'": "Ctrl + I",
        "'\\x0a'": "Ctrl + J", "'\\x0b'": "Ctrl + K", "'\\x0c'": "Ctrl + L",
        "'\\x0d'": "Ctrl + M", "'\\x0e'": "Ctrl + N", "'\\x0f'": "Ctrl + O",
        "'\\x10'": "Ctrl + P", "'\\x11'": "Ctrl + Q", "'\\x12'": "Ctrl + R",
        "'\\x13'": "Ctrl + S", "'\\x14'": "Ctrl + T", "'\\x15'": "Ctrl + U",
        "'\\x16'": "Ctrl + V", "'\\x17'": "Ctrl + W", "'\\x18'": "Ctrl + X",
        "'\\x19'": "Ctrl + Y", "'\\x1a'": "Ctrl + Z", "<48>": "Ctrl + 0",
        "<49>": "Ctrl + 1", "<50>": "Ctrl + 2", "<51>": "Ctrl + 3",
        "<52>": "Ctrl + 4", "<53>": "Ctrl + 5", "<54>": "Ctrl + 6",
        "<55>": "Ctrl + 7", "<56>": "Ctrl + 8", "<57>": "Ctrl + 9",
        "<192>": "Ctrl + `", "<189>": "Ctrl + -", "<187>": "Ctrl + =",
        "\\x1b": "Ctrl + [", "\\x1d": "Ctrl + ]", "\\x1c": "Ctrl + \\",
        "<186>": "Ctrl + ;", "<222>": "Ctrl + '", "<188>": "Ctrl + ,",
        "<190>": "Ctrl + .", "<191>": "Ctrl + /"
    }

    # Multi-key shortcuts stored in separate rows
    multi_key_shortcuts = {
        ("Key.cmd", "Key.tab"): "Win + Tab",
        ("Key.alt_l", "Key.tab"): "Alt + Tab",  # Switch between open apps
        ("Key.alt_l", "Key.f4"): "Alt + F4",  # Close application
        ("Key.ctrl_l", "Key.shift", "Key.esc"): "Ctrl + Shift + Esc",  # Open Task Manager
        ("Key.win", "Key.down"): "Win + Down Arrow",  # Minimize window
        ("Key.win", "Key.up"): "Win + Up Arrow",  # Maximize window
        ("Key.win", "Key.left"): "Win + Left Arrow",  # Snap window to left
        ("Key.win", "Key.right"): "Win + Right Arrow",  # Snap window to right
        ("Key.ctrl_l", "Key.home"): "Ctrl + Home",  # Move to beginning of document
        ("Key.ctrl_l", "Key.end"): "Ctrl + End",  # Move to end of document
        ("Key.shift", "Key.home"): "Shift + Home",  # Select line (start)
        ("Key.shift", "Key.end"): "Shift + End",  # Select line (end)
        ("Key.prtscn",): "PrtScn",  # Capture full screen
        ("Key.win", "Key.shift", "Key.s"): "Win + Shift + S",  # Capture selected area
        ("Key.alt_l", "Key.prtscn"): "Alt + PrtScn",  # Capture active window
        ("Key.ctrl_l", "Key.shift", "Key.t"): "Ctrl + Shift + T",  # Reopen closed tab
        ("Key.f12",): "F12",  # Open Developer Tools
        ("Key.ctrl_l", "Key.shift", "Key.i"): "Ctrl + Shift + I"  # Open Developer Tools (Alternative)
    }

    # Single-key shortcuts that need renaming
    single_key_shortcuts = {
        "Key.home": "Home",
        "Key.end": "End",
        "Key.backspace": "Backspace",
        "Key.delete": "Delete",
        "Key.space": "Space",
        "Key.esc": "Escape",
        "Key.enter": "Enter",
        "Key.tab": "Tab",
        "Key.prtscn": "PrtScn"
    }
    
    # Step 1: Replace Ctrl key mappings
    df["Key Stroke"] = df["Key Stroke"].replace(ctrl_key_mapping)

    # Step 2: Combine multi-key shortcuts
    combined_keystrokes = []
    previous_keys = []

    for index, row in df.iterrows():
        key = row["Key Stroke"]

        if previous_keys:
            potential_shortcut = tuple(previous_keys + [key])
            if potential_shortcut in multi_key_shortcuts:
                combined_keystrokes.append(multi_key_shortcuts[potential_shortcut])
                previous_keys = []  # Reset
                continue  # Skip adding individual keys
            else:
                # If no match, add the previous key separately
                combined_keystrokes.append(previous_keys[0])
                previous_keys = [key]  # Store the current key for next iteration
        else:
            previous_keys.append(key)  # Store first key

    # If any leftover key remains, add it
    if previous_keys:
        combined_keystrokes.append(previous_keys[0])

    # Update DataFrame
    df = df.iloc[:len(combined_keystrokes)].copy()
    df["Key Stroke"] = combined_keystrokes
    df["Key Stroke"] = df["Key Stroke"].replace(single_key_shortcuts)

    return df

def process_keystroke_data(keystroke_data, user_name=None):
    """
    Process keystroke data from a DataFrame or dict.
    
    Args:
        keystroke_data (dict or pd.DataFrame): Raw keystroke data
        user_name (str, optional): User's name for labeling
        
    Returns:
        pd.DataFrame: Processed grouped DataFrame
    """
    try:
        # Convert to DataFrame if needed
        if isinstance(keystroke_data, dict):
            df = pd.DataFrame.from_dict(keystroke_data)
        elif isinstance(keystroke_data, list):
            df = pd.DataFrame(keystroke_data)
        else:
            df = keystroke_data
            
        logger.info(f"Initial DataFrame for {user_name if user_name else 'unknown user'} has {len(df)} rows")
        
        # Add user label if provided
        if user_name:
            df['User'] = user_name
            
        # Convert timestamps to datetime
        df['Timestamp_Press'] = pd.to_datetime(df['Timestamp_Press'])
        df['Timestamp_Release'] = pd.to_datetime(df['Timestamp_Release'])
        
        df.reset_index(drop=True, inplace=True)

        # Clean the data (remove rows with mismatched dates)
        rows_to_drop = []
        for index, row in df.iterrows():
            if row['Timestamp_Press'].date() != row['Timestamp_Release'].date():
                rows_to_drop.append(index)
        
        df.drop(rows_to_drop, axis=0, inplace=True)
        df.reset_index(drop=True, inplace=True)

        df.dropna(inplace=True)
        df.sort_values(by='Timestamp_Release', inplace=True)
        df.reset_index(drop=True, inplace=True)
        
        if user_name==None:
            # Convert hold time to seconds
            if 'Hold Time' in df.columns:
                df['Hold Time (seconds)'] = pd.to_timedelta(df['Hold Time']).dt.total_seconds()
                
                # Remove outliers
                quantile_99 = df['Hold Time (seconds)'].quantile(0.99)
                df = df[df['Hold Time (seconds)'] < quantile_99]

        # Clean Keystrokes
        if 'Key Stroke' in df.columns:
            df['Key Stroke'] = df['Key Stroke'].astype(str)
            df['Key Stroke'] = df['Key Stroke'].str.strip("'")

            # Standardize Keystrokes
            df = standardize_keystrokes(df)
            df = standardize_windows_keystrokes(df)

            # Group data
            df.reset_index(drop=True, inplace=True)
            df["Group"] = df.index // 5
            
            # Create aggregation dictionary based on available columns
            agg_dict = {
                "Timestamp_Press": list,
                "Timestamp_Release": list,
                "Key Stroke": list
            }
            
            if "Application" in df.columns:
                agg_dict["Application"] = list
            if "Hold Time" in df.columns:
                agg_dict["Hold Time"] = list
            if "User" in df.columns:
                agg_dict["User"] = "first"
            
            grouped_df = df.groupby("Group").agg(agg_dict).reset_index(drop=True)
            
            # Remove None columns
            grouped_df = grouped_df.dropna(axis=1, how='all')
        else:
            # If no keystroke data, return as is
            grouped_df = df
            
        logger.info(f"Processed {len(grouped_df)} grouped keystroke entries for {user_name if user_name else 'unknown user'}")
        return grouped_df
    except Exception as e:
        logger.error(f"Error processing keystroke data: {str(e)}")
        raise

def process_keystroke_file(filepath, user_name):
    """
    Process keystroke data from a CSV file.
    
    Args:
        filepath (str): Path to the CSV file
        user_name (str): User's name for labeling
        
    Returns:
        pd.DataFrame: Processed grouped DataFrame
    """
    try:
        df = pd.read_csv(filepath)
        return process_keystroke_data(df, user_name)
    except Exception as e:
        logger.error(f"Error processing keystroke file {filepath}: {str(e)}")
        raise

def categorize_key(key):
    """Categorize a key into a type."""
    key = str(key).strip("'")
    if re.fullmatch(r"Key\.f\d+", key):
        return "Function Key"
    elif re.fullmatch(r"^Key\.media.*", key):
        return "Media Key"
    elif key.isupper():
        return "Upper Alpha"
    elif key.islower():
        return "Lower Alpha"
    elif key.isdigit():
        return "Numeric"
    elif key in "`~!@#$%^&*()-_=+[{]};:'\",<.>/?\\|":
        return "Punctuation"
    elif "Key." in key:
        return "Modifier"
    elif "Backspace" in key or "Delete" in key:
        return "Delete/Backspace"
    elif " + " in key:
        return "Shortcut"
    else:
        return "Other"

def assign_key_section(keystroke):
    """Assign a keyboard section to a keystroke."""
    section1_keys = {"`", "1", "Tab", "Q", "q", "Key.caps_lock", "A", "a", "Key.shift_l", "Z", "z", "Key.alt_l", "Key.ctrl_l", "Key.cmd_l", "Escape", "Key.f1"}
    section2_keys = {"2", "3", "W", "E", "S", "D", "X", "C", "w", "e", "s", "d", "x", "c", "Key.f2", "Key.f3"}
    section3_keys = {"4", "5", "R", "F", "V", "G", "B", "T", "r", "t", "f", "v", "g", "b", "t", "Key.f4", "Key.f5"}
    section4_keys = {"6", "7", "Y", "U", "J", "N", "M", "H", "y", "u", "j", "n", "m", "h", "Key.f6", "Key.f7"}
    section5_keys = {"8", "9", "I", "O", "K", "L", ",", ".", "i", "o", "k", "l", "Key.f8", "Key.f9"}
    section6_keys = {"0", "-", "P", "[", ";", "'", "/", "Key.shift_r", "p", "Key.f10", "Key.f11"}
    section7_keys = {"Key.f12", "Home", "End", "Delete", "\\", "Backspace", "Enter", "Key.shift_r", "Key.page_up", "Key.page_down"}
    section8_keys = {"Key.up", "Key.down", "Key.left", "Key.right"}
    section9_keys = {"Space", "Key.alt_r", "Key.ctrl_l", "Key.cmd_r"}

    if keystroke in section1_keys:
        return "Section 1"
    elif keystroke in section2_keys:
        return "Section 2"
    elif keystroke in section3_keys:
        return "Section 3"
    elif keystroke in section4_keys:
        return "Section 4"
    elif keystroke in section5_keys:
        return "Section 5"
    elif keystroke in section6_keys:
        return "Section 6"
    elif keystroke in section7_keys:
        return "Section 7"
    elif keystroke in section8_keys:
        return "Section 8"
    elif keystroke in section9_keys:
        return "Section 9"
    else:
        return "Other Section"

def compute_and_expand_features_with_prev(row, prev_row=None):
    """
    Compute and expand features from a grouped keystroke row.

    Args:
        row: Current row with grouped keystroke data
        prev_row: Previous row for sequential features

    Returns:
        pd.Series: Expanded features
    """
    press = row["Timestamp_Press"]
    release = row["Timestamp_Release"]
    hold = row["Hold Time"] if "Hold Time" in row else []
    keys = row["Key Stroke"] if "Key Stroke" in row else []
    applications = row["Application"] if "Application" in row else []

    if prev_row is not None and "Timestamp_Press" in prev_row and "Timestamp_Release" in prev_row:
        prev_press = prev_row["Timestamp_Press"]
        prev_release = prev_row["Timestamp_Release"]
        prev_apps = prev_row["Application"] if "Application" in prev_row else None
    else:
        prev_press = prev_release = prev_apps = None

    ppd, rrd, rpd, prd = [], [], [], []

    if prev_press is None:
        ppd.append(0)
    else:
        ppd.append((press[0] - prev_press[-1]).total_seconds())

    for i in range(len(press) - 1):
        ppd.append((press[i + 1] - press[i]).total_seconds())

    if prev_release is None:
        rrd.append(0)
    else:
        rrd.append((release[0] - prev_release[-1]).total_seconds())

    for i in range(len(release) - 1):
        rrd.append((release[i + 1] - release[i]).total_seconds())

    for i in range(len(press)):
        rpd.append((press[i] - release[i - 1]).total_seconds() if i > 0 else 0)
        prd.append((release[i] - press[i - 1]).total_seconds() if i > 0 else 0)

    features = {}
    features.update({f"PPD_{i}": abs(value) for i, value in enumerate(ppd)})
    features.update({f"RRD_{i}": abs(value) for i, value in enumerate(rrd)})
    features.update({f"RPD_{i}": abs(value) for i, value in enumerate(rpd)})
    features.update({f"PRD_{i}": abs(value) for i, value in enumerate(prd)})

    # Convert hold time from timedelta to seconds if needed
    if hold:
        hold_seconds = []
        for ht in hold:
            if isinstance(ht, str):
                try:
                    hold_seconds.append(pd.Timedelta(ht).total_seconds())
                except:
                    hold_seconds.append(0)
            else:
                hold_seconds.append(ht)

        features.update({f"Hold_Time_{i}": hold_seconds[i] for i in range(len(hold_seconds))})

        features["PPD_Sum"] = sum(ppd)
        features["RRD_Sum"] = sum(rrd)
        features["RPD_Sum"] = sum(rpd)
        features["PRD_Sum"] = sum(prd)

        features["Typing_Speed_Avg"] = np.mean(ppd)
        features["Typing_Speed_Max"] = np.max(ppd)
        features["Typing_Speed_Min"] = np.min(ppd)

        features["HT_Sum"] = np.sum(hold_seconds)
        features["Hold_Time_Avg"] = np.mean(hold_seconds)
        features["Hold_Time_Std"] = np.std(hold_seconds)

    # Add key categorization if keys are present
    if keys:
        key_types = [categorize_key(key) for key in keys]
        for i, key_type in enumerate(key_types):
            features[f"Key_Type_{i + 1}"] = key_type

        # Add key section info
        key_sections = [assign_key_section(key) for key in keys]
        for i, key_section in enumerate(key_sections):
            features[f"Key_Section_{i + 1}"] = key_section

    return pd.Series(features)

def expand_features(grouped_df):
    """
    Expand features for all rows in the grouped DataFrame.

    Args:
        grouped_df (pd.DataFrame): Grouped keystroke data

    Returns:
        pd.DataFrame: DataFrame with expanded features
    """
    previous_row = None
    expanded_features_df = []
    
    for idx, row in grouped_df.iterrows():
        expanded_row = compute_and_expand_features_with_prev(row, prev_row=previous_row)
        expanded_features_df.append(expanded_row)
        previous_row = row
        
    expanded_features_df = pd.DataFrame(expanded_features_df)
    return expanded_features_df

def preprocess_keystroke_data(keystroke_data, user_name=None, additional_users=None):
    """
    Main function to preprocess keystroke data and extract features.
    
    Args:
        keystroke_data (dict, DataFrame, or str): Raw keystroke data or filepath
        user_name (str, optional): User's name for labeling
        additional_users (dict): Dictionary with {username: data} for additional users
        
    Returns:
        pd.DataFrame: Processed and feature-expanded DataFrame ready for ML
    """
    try:
        if user_name is None:
            # Process without user information
            if isinstance(keystroke_data, str) and os.path.exists(keystroke_data):
                # It's a filepath
                grouped_df = process_keystroke_file(keystroke_data)
            else:
                # It's data
                grouped_df = process_keystroke_data(keystroke_data)
            
            logger.info(f"Processed {len(grouped_df)} grouped keystroke entries without user information")
            
            # Expand features for the dataset
            expanded_df = expand_features(grouped_df)
            logger.info(f"Generated {len(expanded_df.columns)} features")
            
            # Merge grouped and expanded DataFrames
            final_df = pd.concat([grouped_df, expanded_df], axis=1)
            
        else:
            # Original processing with user information
            if isinstance(keystroke_data, str) and os.path.exists(keystroke_data):
                # It's a filepath
                grouped_df = process_keystroke_file(keystroke_data, user_name)
            else:
                # It's data
                grouped_df = process_keystroke_data(keystroke_data, user_name)
            
            logger.info(f"Processed {len(grouped_df)} grouped keystroke entries for {user_name}")
            
            # Process additional users if provided
            all_grouped_dfs = [grouped_df]
            
            if additional_users:
                for add_user_name, add_user_data in additional_users.items():
                    logger.info(f"Processing additional user: {add_user_name}")
                    
                    if isinstance(add_user_data, str) and os.path.exists(add_user_data):
                        # It's a filepath
                        add_grouped_df = process_keystroke_file(add_user_data, add_user_name)
                    else:
                        # It's data
                        add_grouped_df = process_keystroke_data(add_user_data, add_user_name)
                    
                    logger.info(f"Processed {len(add_grouped_df)} grouped keystroke entries for {add_user_name}")
                    all_grouped_dfs.append(add_grouped_df)
            
            # Combine all user data
            combined_grouped_df = pd.concat(all_grouped_dfs, ignore_index=True)
            logger.info(f"Combined dataset has {len(combined_grouped_df)} total entries")
            
            # Expand features for the combined dataset
            expanded_df = expand_features(combined_grouped_df)
            logger.info(f"Generated {len(expanded_df.columns)} features")
            
            # Merge grouped and expanded DataFrames
            final_df = pd.concat([combined_grouped_df, expanded_df], axis=1)

        # Cleanup unnecessary columns
        columns_to_drop = ['Hold Time', 'Application', 'Key Stroke', 
                          'Timestamp_Release', 'Timestamp_Press']
        
        for col in columns_to_drop:
            if col in final_df.columns:
                final_df = final_df.drop(columns=[col])
        
        # Encode categorical features (except User column if it exists)
        key_section_columns = [col for col in final_df.columns if col.startswith('Key_Section_')]
        key_type_columns = [col for col in final_df.columns if col.startswith('Key_Type_')]
        
        # Simple encoding for demonstration
        # In production, you should use a consistent encoder across all predictions
        for column in key_section_columns:
            if column in final_df.columns:
                # Map to numeric values (consistent mapping would be best)
                section_mapping = {
                    'Section 1': 1, 'Section 2': 2, 'Section 3': 3, 'Section 4': 4,
                    'Section 5': 5, 'Section 6': 6, 'Section 7': 7, 'Section 8': 8,
                    'Section 9': 9, 'Other Section': 0
                }
                final_df[column] = final_df[column].map(section_mapping).fillna(0)
        
        for column in key_type_columns:
            if column in final_df.columns:
                # Map to numeric values
                type_mapping = {
                    'Function Key': 1, 'Media Key': 2, 'Upper Alpha': 3, 'Lower Alpha': 4,
                    'Numeric': 5, 'Punctuation': 6, 'Modifier': 7, 'Delete/Backspace': 8,
                    'Shortcut': 9, 'Other': 0
                }
                final_df[column] = final_df[column].map(type_mapping).fillna(0)
        
        # Handle any remaining non-numeric columns, but keep User column as is if it exists
        for col in final_df.columns:
            if col == 'User' and user_name is not None:
                # Keep User column as categorical/string only if user_name was provided
                continue
            elif pd.api.types.is_object_dtype(final_df[col]):
                try:
                    final_df[col] = pd.to_numeric(final_df[col], errors='coerce')
                except:
                    # If conversion fails, drop the column
                    final_df = final_df.drop(columns=[col])
        
        # Fill NA values except for User column if it exists
        columns_to_fill = [col for col in final_df.columns if col != 'User' or user_name is None]
        final_df[columns_to_fill] = final_df[columns_to_fill].fillna(0)
        
        return final_df
    except Exception as e:
        logger.error(f"Error preprocessing keystroke data: {str(e)}")
        raise

def preprocess_keystroke_files(input_filepath, output_filepath, user_name, additional_users=None):
    """
    Preprocess keystroke data from input CSV and save processed data to output CSV.
    
    Args:
        input_filepath (str): Path to input CSV file
        output_filepath (str): Path to output CSV file
        user_name (str): User's name for labeling
        additional_users (dict): Dictionary with {username: filepath} for additional users
    """
    try:
        logger.info(f"Starting preprocessing for primary user: {user_name}")
        logger.info(f"Input file: {input_filepath}")
        
        # Process the data
        final_df = preprocess_keystroke_data(input_filepath, user_name, additional_users)
        
        # Create directories if needed
        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
        
        # Save to output file
        final_df.to_csv(output_filepath, index=False)
        logger.info(f"Saved preprocessed data to: {output_filepath}")
        
        return final_df
    except Exception as e:
        logger.error(f"Error in preprocessing: {str(e)}")
        raise